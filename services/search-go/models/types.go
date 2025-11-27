package models

// SearchRequest represents the search request body
type SearchRequest struct {
	Vector      []float32 `json:"vector"`
	K           int       `json:"k"`
	UserID      string    `json:"user_id,omitempty"`
	Scope       string    `json:"scope"`
	TextQuery   string    `json:"text_query,omitempty"`
	HybridBoost float32   `json:"hybrid_boost,omitempty"`
}

// SearchResultItem represents a single search result
type SearchResultItem struct {
	ID                string  `json:"id"`
	Score             float32 `json:"score"`
	VecScore          float32 `json:"vec_score"`
	TextScore         float32 `json:"text_score"`
	Caption           string  `json:"caption"`
	CaptionConfidence float32 `json:"caption_confidence"`
	CaptionOrigin     string  `json:"caption_origin"`
	OwnerUserID       string  `json:"owner_user_id,omitempty"`
	Visibility        string  `json:"visibility"`
	CreatedAt         string  `json:"created_at"`
}

// SearchResponse represents the search response body
type SearchResponse struct {
	Results []SearchResultItem `json:"results"`
}
