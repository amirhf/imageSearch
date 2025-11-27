package storage

import (
	"context"
	"fmt"
	"strings"

	"github.com/amirhf/imageSearch/services/search-go/models"
	"github.com/jackc/pgx/v5/pgxpool"
)

type PostgresStore struct {
	pool *pgxpool.Pool
}

func NewPostgresStore(dbURL string) (*PostgresStore, error) {
	config, err := pgxpool.ParseConfig(dbURL)
	if err != nil {
		return nil, err
	}
	pool, err := pgxpool.NewWithConfig(context.Background(), config)
	if err != nil {
		return nil, err
	}
	return &PostgresStore{pool: pool}, nil
}

func (s *PostgresStore) Close() {
	s.pool.Close()
}

func (s *PostgresStore) Search(ctx context.Context, req models.SearchRequest) ([]models.SearchResultItem, error) {
	// Build query
	// Note: We use pgvector's <=> operator for cosine distance (if vectors are normalized) or L2 distance.
	// For OpenCLIP (normalized), <=> is equivalent to 1 - cosine_similarity.
	// We want to maximize similarity, so we sort by distance ASC.
	// Hybrid score = (vec_weight * vec_score) + (text_weight * text_score)

	// Default weights if not provided
	hybridBoost := req.HybridBoost
	if hybridBoost == 0 {
		hybridBoost = 0.3 // Default text weight
	}
	vecWeight := 1.0 - hybridBoost

	// Simplified Hybrid Query (Single Pass)
	simpleQuery := `
		SELECT 
			id,
			(1 - (embed_vector <=> $1)) as vec_score,
			ts_rank_cd(search_vector, websearch_to_tsquery('english', $2)) as text_score,
			caption,
			caption_confidence,
			caption_origin,
			owner_user_id::text,
			visibility,
			created_at::text
		FROM images
		WHERE %s
		ORDER BY (
			(1 - (embed_vector <=> $1)) * $3 + 
			ts_rank_cd(search_vector, websearch_to_tsquery('english', $2)) * $4
		) DESC
		LIMIT $5
	`

	// Build WHERE
	conditions := []string{"1=1"}
	if req.Scope == "mine" {
		if req.UserID == "" {
			return nil, fmt.Errorf("user_id required for scope=mine")
		}
		conditions = append(conditions, fmt.Sprintf("owner_user_id = '%s'", req.UserID))
	} else if req.Scope == "public" {
		conditions = append(conditions, "visibility = 'public'")
	} else { // all
		if req.UserID != "" {
			conditions = append(conditions, fmt.Sprintf("(visibility = 'public' OR owner_user_id = '%s')", req.UserID))
		} else {
			conditions = append(conditions, "visibility = 'public'")
		}
	}

	// Format vector as string for pgvector
	var vecBuilder strings.Builder
	vecBuilder.WriteString("[")
	for i, v := range req.Vector {
		if i > 0 {
			vecBuilder.WriteString(",")
		}
		vecBuilder.WriteString(fmt.Sprintf("%f", v))
	}
	vecBuilder.WriteString("]")
	vecStr := vecBuilder.String()

	whereStr := strings.Join(conditions, " AND ")
	finalQuery := fmt.Sprintf(simpleQuery, whereStr)

	rows, err := s.pool.Query(ctx, finalQuery, vecStr, req.TextQuery, vecWeight, hybridBoost, req.K)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results []models.SearchResultItem
	for rows.Next() {
		var item models.SearchResultItem
		var vecScore, textScore float32
		err := rows.Scan(
			&item.ID,
			&vecScore,
			&textScore,
			&item.Caption,
			&item.CaptionConfidence,
			&item.CaptionOrigin,
			&item.OwnerUserID,
			&item.Visibility,
			&item.CreatedAt,
		)
		if err != nil {
			return nil, err
		}
		item.VecScore = vecScore
		item.TextScore = textScore
		item.Score = (vecScore * float32(vecWeight)) + (textScore * float32(hybridBoost))
		results = append(results, item)
	}
	return results, nil
}
