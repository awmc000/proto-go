package main


import (
	"bufio"
	"fmt"
	"log"
	"net"
	"strings"
)

func main() {

	listener, err := net.listen("tcp", "7007")
	if err != nil {
		log.Fatal("收听异常：", err)
	}

	defer listener.Close()

	for {
		
		conn, err := listener.Accept()
		if err != nil {
			log.Println("链接异常：", err)
			continue

		go handleConnection(conn)
	}
}

func handleConnection(conn net.Conn) {
	defer conn.Close()

	reader := bufio.NewReader(conn)
	message, err := reader.ReadString('\n')
	if err != nil {
		log.Printf("收看异常：%v", err)
		return
	}

	_, err = conn.Write([]byte(message))
	if err != nil {
		log.Printf("写作异常：%v", err)
	}
}
