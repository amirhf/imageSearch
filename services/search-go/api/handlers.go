package api

import (
	"encoding/json"
	"net/http"

	"github.com/amirhf/imageSearch/services/search-go/models"
	"github.com/amirhf/imageSearch/services/search-go/storage"
)

type Handler struct {
	store *storage.PostgresStore
}

func NewHandler(store *storage.PostgresStore) *Handler {
	return &Handler{store: store}
}

func (h *Handler) Search(w http.ResponseWriter, r *http.Request) {
	var req models.SearchRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate
	if len(req.Vector) != 512 {
		http.Error(w, "Vector must be 512 dimensions", http.StatusBadRequest)
		return
	}
	if req.K <= 0 {
		req.K = 10
	}
	if req.Scope == "" {
		req.Scope = "all"
	}

	// Call Storage
	results, err := h.store.Search(r.Context(), req)
	if err != nil {
		http.Error(w, "Internal server error: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Response
	resp := models.SearchResponse{Results: results}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}
