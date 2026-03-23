package main


import (
	"log"
	"net"
	"io"
)

func main() {

	listener, err := net.Listen("tcp", ":7007")
	if err != nil {
		log.Fatal("收听异常：", err)
	}

	defer listener.Close()

	for {
		
		conn, err := listener.Accept()
		if err != nil {
			log.Println("链接异常：", err)
			continue
		}
		go handleConnection(conn)
	}
}

func handleConnection(conn net.Conn) {
	defer conn.Close()
	io.Copy(conn, conn)
}
