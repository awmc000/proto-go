package main

import "fmt"

func main() {

	i := 1

	for i <= 5 {
		fmt.Println(i)
		i += 1
	}

	for {
		fmt.Println("死循环")
	}

}
