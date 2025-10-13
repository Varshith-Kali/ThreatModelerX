package main

import (
	"database/sql"
	"fmt"
	"net/http"
	"os/exec"
	"strings"

	"github.com/gin-gonic/gin"
	_ "github.com/mattn/go-sqlite3"
)

const (
	API_KEY        = "hardcoded_go_secret_key_12345"
	ADMIN_PASSWORD = "admin123"
)

func main() {
	r := gin.Default()
	
	// Enable debug mode
	gin.SetMode(gin.DebugMode)

	r.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message":   "Vulnerable Go Gin Demo App",
			"endpoints": []string{"/user/:id", "/search", "/exec", "/admin"},
		})
	})

	r.GET("/user/:id", func(c *gin.Context) {
		id := c.Param("id")
		
		// SQL Injection vulnerability
		db, _ := sql.Open("sqlite3", ":memory:")
		defer db.Close()
		
		// Create a test table
		db.Exec("CREATE TABLE IF NOT EXISTS users (id INTEGER, username TEXT, password TEXT)")
		db.Exec("INSERT INTO users VALUES (1, 'admin', 'password123')")
		
		// Vulnerable query
		query := fmt.Sprintf("SELECT * FROM users WHERE id = %s", id)
		rows, err := db.Query(query)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		defer rows.Close()
		
		var userId int
		var username, password string
		if rows.Next() {
			rows.Scan(&userId, &username, &password)
			c.JSON(http.StatusOK, gin.H{"user": gin.H{"id": userId, "username": username, "password": password}})
		} else {
			c.JSON(http.StatusNotFound, gin.H{"message": "User not found"})
		}
	})

	r.GET("/search", func(c *gin.Context) {
		q := c.Query("q")
		
		// SQL Injection vulnerability
		db, _ := sql.Open("sqlite3", ":memory:")
		defer db.Close()
		
		// Create a test table
		db.Exec("CREATE TABLE IF NOT EXISTS products (id INTEGER, name TEXT, price REAL)")
		db.Exec("INSERT INTO products VALUES (1, 'Product 1', 19.99)")
		
		// Vulnerable query
		query := fmt.Sprintf("SELECT * FROM products WHERE name LIKE '%%%s%%'", q)
		rows, err := db.Query(query)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		defer rows.Close()
		
		var results []gin.H
		for rows.Next() {
			var id int
			var name string
			var price float64
			rows.Scan(&id, &name, &price)
			results = append(results, gin.H{"id": id, "name": name, "price": price})
		}
		
		c.JSON(http.StatusOK, gin.H{"results": results})
	})

	r.GET("/exec", func(c *gin.Context) {
		cmd := c.Query("cmd")
		
		// Command injection vulnerability
		command := exec.Command("sh", "-c", cmd)
		output, err := command.CombinedOutput()
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		
		c.JSON(http.StatusOK, gin.H{"output": string(output)})
	})

	r.GET("/admin", func(c *gin.Context) {
		username := c.Query("username")
		password := c.Query("password")
		
		// Hardcoded credentials vulnerability
		if username == "admin" && password == ADMIN_PASSWORD {
			c.JSON(http.StatusOK, gin.H{"message": "Welcome admin!", "token": API_KEY})
		} else {
			c.JSON(http.StatusUnauthorized, gin.H{"message": "Access denied"})
		}
	})

	r.Run(":8081")
}