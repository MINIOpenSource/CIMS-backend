package service

import (
	"sync"

	"github.com/MINIOpenSource/CIMS-backend/internal/proto/Protobuf/Enum"
	"github.com/MINIOpenSource/CIMS-backend/internal/proto/Protobuf/Server"
)

type CommandService struct {
	// Map of ClientID -> Channel for sending commands
	clientChans map[string]chan *Server.ClientCommandDeliverScRsp
	mu          sync.RWMutex
}

var globalCommandService *CommandService

func GetCommandService() *CommandService {
	if globalCommandService == nil {
		globalCommandService = &CommandService{
			clientChans: make(map[string]chan *Server.ClientCommandDeliverScRsp),
		}
	}
	return globalCommandService
}

// RegisterClientChannel registers a channel for a connected gRPC client
func (s *CommandService) RegisterClientChannel(clientID string, ch chan *Server.ClientCommandDeliverScRsp) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.clientChans[clientID] = ch
}

// UnregisterClientChannel removes the channel
func (s *CommandService) UnregisterClientChannel(clientID string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.clientChans, clientID)
}

// SendCommand sends a command to a specific client
func (s *CommandService) SendCommand(clientID string, cmdType Enum.CommandTypes, payload []byte) bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	ch, ok := s.clientChans[clientID]

	if !ok {
		return false
	}

	select {
	case ch <- &Server.ClientCommandDeliverScRsp{
		RetCode: Enum.Retcode_Success,
		Type:    cmdType,
		Payload: payload,
	}:
		return true
	default:
		// Channel full or blocked
		return false
	}
}
