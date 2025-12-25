package grpc

import (
	"fmt"
	"io"
	"log"
	"sync"

	"github.com/MINIOpenSource/CIMS-backend/internal/proto/Protobuf/Enum"
	"github.com/MINIOpenSource/CIMS-backend/internal/proto/Protobuf/Server"
	"github.com/MINIOpenSource/CIMS-backend/internal/proto/Protobuf/Service"
	"github.com/MINIOpenSource/CIMS-backend/internal/service"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/peer"
)

type ClientCommandDeliverServer struct {
	Service.UnimplementedClientCommandDeliverServer
	commandService *service.CommandService
	clientService  *service.ClientService
}

func NewClientCommandDeliverServer() *ClientCommandDeliverServer {
	return &ClientCommandDeliverServer{
		commandService: service.GetCommandService(),
		clientService:  service.NewClientService(),
	}
}

func (s *ClientCommandDeliverServer) ListenCommand(stream Service.ClientCommandDeliver_ListenCommandServer) error {
	md, ok := metadata.FromIncomingContext(stream.Context())
	if !ok {
		return fmt.Errorf("missing metadata")
	}

	cuidList := md.Get("cuid")
	if len(cuidList) == 0 {
		return fmt.Errorf("missing cuid in metadata")
	}
	clientID := cuidList[0]

	p, _ := peer.FromContext(stream.Context())
	clientIP := p.Addr.String()

	log.Printf("Client connected: %s (%s)", clientID, clientIP)

	cmdChan := make(chan *Server.ClientCommandDeliverScRsp, 10)
	s.commandService.RegisterClientChannel(clientID, cmdChan)
	// Ensure Unregister happens before Close to avoid race conditions in SendCommand
	defer close(cmdChan)
	defer s.commandService.UnregisterClientChannel(clientID)

	var streamMu sync.Mutex

	// Send commands
	go func() {
		for cmd := range cmdChan {
			streamMu.Lock()
			err := stream.Send(cmd)
			streamMu.Unlock()
			if err != nil {
				log.Printf("Error sending command to %s: %v", clientID, err)
				return
			}
		}
	}()

	// Receive heartbeats
	for {
		req, err := stream.Recv()
		if err == io.EOF {
			log.Printf("Client disconnected: %s", clientID)
			return nil
		}
		if err != nil {
			log.Printf("Error receiving from %s: %v", clientID, err)
			return err
		}

		if req.Type == Enum.CommandTypes_Ping {
			_ = s.clientService.UpdateHeartbeat(clientID, clientIP)
			pong := &Server.ClientCommandDeliverScRsp{
				RetCode: Enum.Retcode_Success,
				Type:    Enum.CommandTypes_Pong,
			}
			streamMu.Lock()
			err := stream.Send(pong)
			streamMu.Unlock()
			if err != nil {
				log.Printf("Error sending Pong to %s: %v", clientID, err)
				return err
			}
		}
	}
}
