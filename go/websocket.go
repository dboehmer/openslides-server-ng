package main

import (
	"fmt"
	"net/http"

	"github.com/gorilla/websocket"
)

// AutoupdateMessage is a message type that is send from the server to the client.
type AutoupdateMessage struct {
	Type    string                   `json:"type"`
	Changed map[string][]interface{} `json:"changed"`
	Deleted map[string][]int         `json:"deleted"`
	AllData bool                     `json:"all_data"`
}

// Client represents a connection from one client.
type Client struct {
	conn *websocket.Conn
}

var clients map[*Client]struct{}

func init() {
	clients = make(map[*Client]struct{})
}

func (c *Client) register() {
	clients[c] = struct{}{}
	debug(
		fmt.Sprintf("New connection, currently %d connected clients", len(clients)),
	)
}

func (c *Client) unregister() {
	delete(clients, c)
	debug(
		fmt.Sprintf("Lost connection, currently %d connected clients", len(clients)),
	)
}

func (c *Client) connected() {
	// client connects to server
	allData := make(map[string][]interface{})
	for collection, data := range getDatabase() {
		allData[collection] = make([]interface{}, 0)
		for _, element := range data {
			allData[collection] = append(allData[collection], element)
		}
	}
	c.send(
		AutoupdateMessage{
			Type:    "autoupdate",
			Changed: allData,
			Deleted: nil,
			AllData: true,
		},
	)
}

func (c *Client) recv(message interface{}) {

}

func (c *Client) send(message AutoupdateMessage) error {
	return c.conn.WriteJSON(message)
}

// SendToAll sends a message to all clients
func SendToAll(message AutoupdateMessage) {
	// TODO: The python implementation uses this to encode the message only
	// once to json.
	for client := range clients {
		client.send(message)
	}
}

func wsHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := websocket.Upgrade(w, r, w.Header(), 1024, 1024)
	if err != nil {
		http.Error(w, "Could not open websocket connection", http.StatusBadRequest)
	}

	client := Client{conn}
	client.register()
	defer client.unregister()

	client.connected()
}

func serve(host string) {
	http.HandleFunc("/", wsHandler)

	fmt.Printf("Started Server on %s\n", host)
	panic(http.ListenAndServe(host, nil))
}
