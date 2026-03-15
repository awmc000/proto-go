// prime time
package main

import (
	"encoding/json"
	"fmt"
	"net"
	"log"
	"bufio"
)

type request struct {
	Method	string
	Number	int
}

func handleConnection(c net.Conn) {
	defer c.Close()

	reader := bufio.NewReader(c)
	msg, err := reader.ReadString('\n')
	if err != nil {
		log.Fatal("Listening err:", err)
	}
	req := request{}
	json.Unmarshal([]byte(msg), &req)
	fmt.Println(req)
}

func main() {
	listener, err := net.Listen("tcp", ":7007")
	if err != nil {
		log.Fatal("Listening err:", err)
	}

	defer listener.Close()

	for {
		c, err := listener.Accept()
		if err != nil {
			log.Fatal("Accepting err:", err)
			continue
		}
		go handleConnection(c)
	}
}
