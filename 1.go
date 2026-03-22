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
	Method	string `json:"method"`
	Number	int `json:"number"`
}

type response struct {
	Method string `json:"method"`
	Prime bool `json:"prime"`
}

func handleConnection(c net.Conn) {
	defer c.Close()

	for {
		// Create a new buf reader and get line.
		reader := bufio.NewReader(c)
		msg, err := reader.ReadString('\n')
		fmt.Println("msg: ", msg)
		// Err fires if a string could not be read.
		if err != nil {
			c.Write([]byte("Err!"))
			log.Fatal("Listening err:", err)
			break
		}
		req := request{}
		err = json.Unmarshal([]byte(msg), &req)
		// Err if malformed.
		if err != nil {
			c.Write([]byte("Err!"))
			log.Fatal("unmarshalling err:", err)
			break
		}
		fmt.Println("req: ", req)
		if (req.Method == "isPrime") {
			res := &response{
				Method: "isPrime",
				Prime: false}
			res_json, _ := json.Marshal(res)
			fmt.Println("res: ", res_json)
			c.Write(res_json)
		}
	}
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
