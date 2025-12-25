package service

import (
	"sync"
	"testing"
	"time"

	"github.com/MINIOpenSource/CIMS-backend/internal/proto/Protobuf/Enum"
	"github.com/MINIOpenSource/CIMS-backend/internal/proto/Protobuf/Server"
)

func TestCommandService_SendCommand_ThreadSafety(t *testing.T) {
	s := &CommandService{
		clientChans: make(map[string]chan *Server.ClientCommandDeliverScRsp),
	}

	clientID := "test-client"
	ch := make(chan *Server.ClientCommandDeliverScRsp, 10)

	s.RegisterClientChannel(clientID, ch)

	// Simulate concurrent access: SendCommand vs Unregister/Close

	var wg sync.WaitGroup
	wg.Add(2)

	// Sender routine
	go func() {
		defer wg.Done()
		for i := 0; i < 1000; i++ {
			s.SendCommand(clientID, Enum.CommandTypes_Ping, []byte{})
			time.Sleep(100 * time.Microsecond)
		}
	}()

	// Unregister/Closer routine
	go func() {
		defer wg.Done()
		time.Sleep(50 * time.Millisecond) // Let some sends happen

		// Simulate the sequence in ListenCommand
		s.UnregisterClientChannel(clientID)
		close(ch)
	}()

	wg.Wait()

	// If the code is buggy (SendCommand does not hold lock), we might see a panic: "send on closed channel"
	// Because SendCommand might get the channel, then Unregister/Close happens, then SendCommand sends.
	// With the fix, SendCommand holds lock.
	// If it gets lock before Unregister, it sends.
	// If Unregister gets lock, it removes from map. SendCommand (later) will not find it.
	// close(ch) happens after Unregister.
}
