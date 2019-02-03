package main

import (
	"io/ioutil"
	"log"
	"sync"

	"github.com/vmihailenco/msgpack"
)

const dbPath = "../all_data.msgpack"

type element map[string]interface{}
type collection map[int]element

// ElementID reporesents an element in the database
type ElementID struct {
	Collection string
	ID         int
}

// AllDataType is a copy of the database + a list of changed elements
type AllDataType struct {
	Database        map[string]collection
	ChangedElements []ElementID
}

func (allData *AllDataType) addElement(collection string, element map[string]interface{}) int {
	newID := 0
	for key := range allData.Database[collection] {
		newID = max(newID, key)
	}
	newID++
	element["id"] = newID
	allData.Database[collection][newID] = element
	allData.ChangedElements = append(allData.ChangedElements, ElementID{collection, newID})
	return newID
}

var database map[string]collection
var databaseWriteLock = sync.Mutex{}

func init() {
	content, err := ioutil.ReadFile(dbPath)
	if err != nil {
		log.Fatalf("Can not read DB file: %s\n", err)
	}
	if err = msgpack.Unmarshal(content, &database); err != nil {
		log.Fatalf("Can not parse DB file: %s\n", err)
	}
}

func getAllData() *AllDataType {
	var allData AllDataType
	allData.Database = getDatabase()
	allData.ChangedElements = make([]ElementID, 0)
	return &allData
}

func saveDatabase(allData *AllDataType) error {
	database = allData.Database
	return nil
}

func getDatabase() map[string]collection {
	return copyDatabase(database)
}

func copyDatabase(input map[string]collection) map[string]collection {
	b, err := msgpack.Marshal(input)
	if err != nil {
		log.Fatalf("Can not copy a map that can not be packed into msgpack.")
	}
	var out map[string]collection
	if err = msgpack.Unmarshal(b, &out); err != nil {
		log.Fatalf("The packed msg pack could not be converted back to map.")
	}
	return out
}
