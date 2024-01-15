# Use the official Golang image with Alpine
FROM golang:alpine

# Set the working directory inside the container
WORKDIR /app

# Copy the Go Modules manifests
COPY go.mod ./
COPY go.sum ./

# Download Go modules
RUN go mod download

# Copy the source code
COPY *.go ./

# Build the application
RUN go build -o /step-trigger-server

# Expose port 8080
EXPOSE 8080

# Command to run the executable
CMD ["/step-trigger-server"]
