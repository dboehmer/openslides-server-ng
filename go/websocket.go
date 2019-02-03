package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

var clients map[*Client]struct{}
var clientsLock sync.Mutex

func init() {
	clients = make(map[*Client]struct{})
}

// AutoupdateMessage is a message to the client when the server sends elements.
type AutoupdateMessage struct {
	Type    string                   `json:"type"`
	Changed map[string][]interface{} `json:"changed"`
	Deleted map[string][]int         `json:"deleted"`
	AllData bool                     `json:"all_data"`
}

// ErrorMessage is a message send to the client when there is an error.
type ErrorMessage struct {
	Type       string `json:"type"`
	ResponseID string `json:"response-id"`
	Error      string `json:"error"`
}

// ResponseActionMessage is a message to the client when the client sends some actions.
type ResponseActionMessage struct {
	Type       string                   `json:"type"`
	ResponseID string                   `json:"response-id"`
	Responses  []map[string]interface{} `json:"responses"`
}

// RecvMessage contains a message id and a list of ActionData.
type RecvMessage struct {
	ID      string       `json:"id"`
	Actions []ActionData `json:"actions"`
}

// Client represents a connection from one client.
type Client struct {
	conn     *websocket.Conn
	sendChan chan []byte
}

// NewClient creates a new client connection
func NewClient(conn *websocket.Conn) *Client {
	client := Client{conn, make(chan []byte)}
	go client.handleSend()
	return &client
}

func (c *Client) register() {
	clientsLock.Lock()
	clients[c] = struct{}{}
	clientsLock.Unlock()
	debug(
		fmt.Sprintf("New connection, currently %d connected clients", len(clients)),
	)
}

func (c *Client) unregister() {
	clientsLock.Lock()
	delete(clients, c)
	clientsLock.Unlock()
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
	c.send(AutoupdateMessage{
		Type:    "autoupdate",
		Changed: allData,
		Deleted: make(map[string][]int),
		AllData: true,
	})
}

func (c *Client) send(message interface{}) error {
	b, err := json.Marshal(message)
	if err != nil {
		return err
	}
	c.sendChan <- b
	return nil
}

func (c *Client) recv(message RecvMessage) {
	prepareActions(message.Actions, time.Now().Unix())
	allData, returnValues, err := handleActions(message.Actions)
	if err != nil {
		c.send(ErrorMessage{
			Type:       "response",
			Error:      err.Error(),
			ResponseID: message.ID,
		})
		return
	}
	c.send(ResponseActionMessage{
		Type:       "response",
		ResponseID: message.ID,
		Responses:  returnValues,
	})
	InformChangedElements(allData)
}

func (c *Client) handleSend() {
	for message := range c.sendChan {
		c.conn.WriteMessage(websocket.TextMessage, message)
	}
}

// SendToAll sends a message to all clients
func SendToAll(message interface{}) error {
	b, err := json.Marshal(message)
	if err != nil {
		return err
	}
	for client := range clients {
		client.sendChan <- b
	}
	return nil
}

func wsHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := websocket.Upgrade(w, r, w.Header(), 1024, 1024)
	if err != nil {
		http.Error(w, "Could not open websocket connection", http.StatusBadRequest)
	}

	client := NewClient(conn)
	defer close(client.sendChan)
	defer conn.Close()
	client.register()
	defer client.unregister()

	client.connected()
	for {
		messageType, p, err := conn.ReadMessage()
		if err != nil {
			if _, ok := err.(*websocket.CloseError); ok {
				break
			}
			log.Panicf("Websocket error: %s\n", err)
			return
		}
		if messageType != websocket.TextMessage {
			log.Panicf("Supports only text messages\n")
		}
		var message RecvMessage
		err = json.Unmarshal(p, &message)
		if err != nil {
			log.Panicf("Can not convert message to json: %s\n", err)
		}
		client.recv(message)
	}

}

// Serve starts the webserver and listens for websocket connections
func Serve(host string) {
	http.HandleFunc("/", wsHandler)

	fmt.Printf("Started Server on %s\n", host)
	panic(http.ListenAndServe(host, nil))
}
