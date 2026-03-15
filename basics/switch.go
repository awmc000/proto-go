package main

import (
	"fmt"
	"time"
)

func main() {

	switch time.Now().Weekday() {
		case time.Saturday, time.Sunday:
			fmt.Println("周末啦！")
		default:
			fmt.Println("-_o")
	}

	whatAmI := func(i interface{}) {
		switch t:= i.(type) {
	}

}
