// prime time
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"net"
)

type request struct {
	Method string `json:"method"`
	Number int    `json:"number"`
}

type response struct {
	Method string `json:"method"`
	Prime  bool   `json:"prime"`
}

func isPrime(n int) bool {
	if n <= 1 {
		return false
	}
	for i := 2; i*i <= n; i++ {
		if n%i == 0 {
			return false
		}
	}
	return true
}

func handleConnection(c net.Conn) {
	defer c.Close()

	reader := bufio.NewReader(c)

	for {
		// Create a new buf reader and get line.
		msg, err := reader.ReadString('\n')

		// Err if a string could not be read.
		if err != nil {
			c.Write([]byte("Read err!"))
			log.Println("Reading err:", err)
			return
		}
		req := request{}
		err = json.Unmarshal([]byte(msg), &req)

		// Err if malformed.
		if err != nil {
			c.Write([]byte("Unmarshalling err!"))
			log.Println("Unmarshalling err:", err)
			return
		}

		if req.Method == "isPrime" {
			res := &response{
				Method: "isPrime",
				Prime:  isPrime(req.Number)}
			res_json, _ := json.Marshal(res)
			fmt.Println("res: ", string(res_json))
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
			log.Println("Accepting err:", err)
			continue
		}
		go handleConnection(c)
	}
}
