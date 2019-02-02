package main

import "fmt"

// DEBUG desides, if debug messages are shown
const DEBUG = true

func debug(message string) {
	if DEBUG {
		fmt.Println(message)
	}
}
