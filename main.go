package main

import (
	"encoding/json"
	"math/rand"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

type StepPayload struct {
	StepName          string  `json:"step_name"`
	RepoPath          string  `json:"repo_path"`
	CommitHash        string  `json:"commit_hash"`
	SimulateStatus    *string `json:"simulate_status,omitempty"`
	SimulateBuildTime *int    `json:"simulate_build_time,omitempty"`
}

type Response struct {
	BuildLogs  string `json:"build_logs"`
	Status     string `json:"status"`
	DurationMs int    `json:"duration_ms"`
}

var buildLock = sync.Mutex{}
var testLock = sync.Mutex{}

func stepTriggerHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("[Step Handler] Received request from %v", r.RemoteAddr)
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	var payload StepPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	startTime := time.Now()

	logs := "step '" + payload.StepName + "' build started!"
	logs += "\nRepo path: " + payload.RepoPath
	logs += "\nCommit hash: " + payload.CommitHash

	status := "Success"
	switch payload.StepName {
	case "lint":
		logs += "\nLinting..."
		// simulate a short random step that always succeeds
		time.Sleep(time.Duration(rand.Intn(100)) * time.Millisecond)
	case "build":
		logs += "\nBuilding..."
		buildTime := rand.Intn(1000) // Random build time in milliseconds
		if payload.SimulateBuildTime != nil {
			buildTime = *payload.SimulateBuildTime
		}
		// Check if the lock is available. If not, write something to the logs and wait until it is.
		// This is to simulate a shared resource during the build.
		if !buildLock.TryLock() {
			log.Warn().Msg("Building lock is not available!")
			logs += "\nWaiting for lock..."
			buildLock.Lock()
		}
		defer buildLock.Unlock()

		// Simulate build time
		logs += "\nSimulating build for step '" + payload.StepName + "'..."
		time.Sleep(time.Duration(buildTime) * time.Millisecond)

		if payload.SimulateStatus != nil {
			status = *payload.SimulateStatus
		} else if rand.Intn(2) == 0 {
			status = "Failure"
		}
	case "test":
		logs += "\nTesting..."
		buildTime := rand.Intn(1000) // Random build time in milliseconds
		if payload.SimulateBuildTime != nil {
			buildTime = *payload.SimulateBuildTime
		}
		// Check if the lock is available. If not, write something to the logs and wait until it is.
		// This is to simulate a shared resource during the build.
		if !testLock.TryLock() {
			log.Warn().Msg("Testing lock is not available!")
			logs += "\nWaiting for lock..."
			testLock.Lock()
		}
		defer testLock.Unlock()

		// Simulate build time
		logs += "\nSimulating build for step '" + payload.StepName + "'..."
		time.Sleep(time.Duration(buildTime) * time.Millisecond)

		if payload.SimulateStatus != nil {
			status = *payload.SimulateStatus
		} else if rand.Intn(2) == 0 {
			status = "Failure"
		}

		// Randomly, 1 of 5 times, simulate a total server crash because of a
		// test failure (like a Segfault in the test runner, for example),
		// unless the ORCA_CI_SERVER_CRASHABLE environment variable is set to
		// "false".

		if os.Getenv("ORCA_CI_SERVER_CRASHABLE") == "false" {
			break
		}
		if rand.Intn(5) == 0 {
			log.Fatal().Msg("Oh no! The tests caused a server crash!")
		}
	default:
		log.Error().Msg("Unknown step provided")
		http.Error(w, "Unknown step!", http.StatusBadRequest)
		return
	}

	duration := int(time.Since(startTime).Milliseconds())

	logs += "\nStep '" + payload.StepName + "' completed with status: " + status

	response := Response{
		BuildLogs:  logs,
		Status:     status,
		DurationMs: duration,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

const DEFAULT_SERVER_ADDR = ":8080"

func main() {
	log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr})
	serverAddr := os.Getenv("ORCA_STEP_RUNNER_SERVER_ADDR")
	if serverAddr == "" {
		serverAddr = DEFAULT_SERVER_ADDR
	}

	log.Printf("Starting server on %s...", serverAddr)
	http.HandleFunc("/step/trigger", stepTriggerHandler)
	log.Err(http.ListenAndServe(serverAddr, nil)).Msg("Server done")
}
