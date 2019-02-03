package main

import "fmt"

// DEBUG desides, if debug messages are shown
const DEBUG = false

func debug(message string) {
	if DEBUG {
		fmt.Println(message)
	}
}

func max(a int, b int) int {
	if a > b {
		return a
	}
	return b
}
