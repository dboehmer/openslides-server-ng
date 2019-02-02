package main

import (
	"io/ioutil"
	"log"

	"github.com/vmihailenco/msgpack"
)

type element map[string]interface{}
type collection map[int]element

var database map[string]collection

const dbPath = "../all_data.msgpack"

func init() {
	content, err := ioutil.ReadFile(dbPath)
	if err != nil {
		log.Fatalf("Can not read DB file: %s\n", err)
	}
	if err = msgpack.Unmarshal(content, &database); err != nil {
		log.Fatalf("Can not parse DB file: %s\n", err)
	}
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
