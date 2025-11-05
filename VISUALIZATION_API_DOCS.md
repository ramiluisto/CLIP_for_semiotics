# Visualization API Documentation

Complete API reference for generating, managing, and retrieving visualizations in CLIP for Humanists.

## Base URL

```
/api/v1/visualizations/
```

## Authentication

All endpoints require authentication. Include your token in the Authorization header:

```
Authorization: Token your-api-token-here
```

---

## Endpoints

### 1. List Visualizations

Get all visualizations you have access to.

**Endpoint:** `GET /api/v1/visualizations/`

**Query Parameters:**
- `viz_type` (optional): Filter by type (`heatmap`, `correlation`, `image_grid`, `map`)
- `analysis` (optional): Filter by analysis ID
- `file_format` (optional): Filter by format (`png`, `svg`, `pdf`, `html`)
- `search` (optional): Search in title or analysis name
- `ordering` (optional): Sort results (`-created_at`, `created_at`, `viz_type`)
- `page` (optional): Page number for pagination

**Example Request:**
```bash
curl -X GET "https://your-domain.com/api/v1/visualizations/?viz_type=heatmap&ordering=-created_at" \
  -H "Authorization: Token your-api-token"
```

**Example Response:**
```json
{
  "count": 15,
  "next": "https://your-domain.com/api/v1/visualizations/?page=2",
  "previous": null,
  "results": [
    {
      "id": 42,
      "title": "Urban Analysis - Similarity Heatmap",
      "viz_type": "heatmap",
      "file_format": "png",
      "file_path": "/media/visualizations/analysis_7/heatmap_20251105_143022.png",
      "file_size": 245678,
      "config": {
        "colormap": "viridis",
        "dpi": 100,
        "show_values": false
      },
      "analysis": 7,
      "created_by": 3,
      "created_at": "2025-11-05T14:30:22Z"
    }
  ]
}
```

---

### 2. Get Single Visualization

Retrieve detailed information about a specific visualization.

**Endpoint:** `GET /api/v1/visualizations/{id}/`

**Example Request:**
```bash
curl -X GET "https://your-domain.com/api/v1/visualizations/42/" \
  -H "Authorization: Token your-api-token"
```

**Example Response:**
```json
{
  "id": 42,
  "title": "Urban Analysis - Similarity Heatmap",
  "viz_type": "heatmap",
  "file_format": "png",
  "file_path": "/media/visualizations/analysis_7/heatmap_20251105_143022.png",
  "file_size": 245678,
  "config": {
    "colormap": "viridis",
    "dpi": 100,
    "show_values": false
  },
  "analysis": {
    "id": 7,
    "name": "Urban Architecture Analysis",
    "dataset": 12,
    "status": "completed"
  },
  "created_by": {
    "id": 3,
    "username": "researcher1",
    "email": "researcher@example.com"
  },
  "created_at": "2025-11-05T14:30:22Z",
  "download_url": "/media/visualizations/analysis_7/heatmap_20251105_143022.png"
}
```

---

### 3. Generate Custom Visualization

Create a new visualization with custom configuration.

**Endpoint:** `POST /api/v1/visualizations/`

**Request Body:**
```json
{
  "analysis_id": 7,
  "viz_type": "heatmap",
  "title": "My Custom Heatmap",
  "config": {
    "colormap": "coolwarm",
    "dpi": 150,
    "show_values": true
  },
  "async": true
}
```

**Parameters:**
- `analysis_id` (required): ID of the analysis to visualize
- `viz_type` (required): Type of visualization (`heatmap`, `correlation`, `image_grid`)
- `title` (optional): Custom title for the visualization
- `config` (optional): Configuration object (see Configuration Options below)
- `async` (optional, default: true): Generate asynchronously

**Example Request (Async):**
```bash
curl -X POST "https://your-domain.com/api/v1/visualizations/" \
  -H "Authorization: Token your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": 7,
    "viz_type": "correlation",
    "async": true
  }'
```

**Example Response (Async):**
```json
{
  "status": "generating",
  "task_id": "abc123-def456-ghi789",
  "message": "Visualization is being generated in the background"
}
```

**Example Request (Sync):**
```bash
curl -X POST "https://your-domain.com/api/v1/visualizations/" \
  -H "Authorization: Token your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": 7,
    "viz_type": "heatmap",
    "async": false
  }'
```

**Example Response (Sync):**
```json
{
  "id": 43,
  "title": "Urban Architecture Analysis - Similarity Heatmap",
  "viz_type": "heatmap",
  "file_format": "png",
  "file_path": "/media/visualizations/analysis_7/heatmap_20251105_150122.png",
  "file_size": 248901,
  "analysis": 7,
  "created_at": "2025-11-05T15:01:22Z"
}
```

---

### 4. Generate Default Visualizations

Generate all three default visualizations (heatmap, correlation, image grid) for an analysis.

**Endpoint:** `POST /api/v1/visualizations/generate_default/`

**Request Body:**
```json
{
  "analysis_id": 7,
  "async": true
}
```

**Parameters:**
- `analysis_id` (required): ID of the analysis
- `async` (optional, default: true): Generate asynchronously

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/v1/visualizations/generate_default/" \
  -H "Authorization: Token your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": 7,
    "async": true
  }'
```

**Example Response (Async):**
```json
{
  "status": "generating",
  "task_id": "xyz789-abc123-def456",
  "message": "Generating default visualizations in the background",
  "expected_count": 3
}
```

**Example Response (Sync):**
```json
{
  "created": [
    {
      "id": 44,
      "title": "Urban Architecture Analysis - Similarity Heatmap",
      "viz_type": "heatmap"
    },
    {
      "id": 45,
      "title": "Urban Architecture Analysis - Concept Correlation Matrix",
      "viz_type": "correlation"
    },
    {
      "id": 46,
      "title": "Urban Architecture Analysis - Image Grid",
      "viz_type": "image_grid"
    }
  ],
  "errors": [],
  "success_count": 3,
  "error_count": 0
}
```

---

### 5. Regenerate Visualization

Create a new version of an existing visualization with updated data.

**Endpoint:** `POST /api/v1/visualizations/{id}/regenerate/`

**Request Body:**
```json
{
  "config": {
    "colormap": "plasma",
    "dpi": 200
  },
  "async": true
}
```

**Parameters:**
- `config` (optional): New configuration (defaults to existing config)
- `async` (optional, default: true): Generate asynchronously

**Example Request:**
```bash
curl -X POST "https://your-domain.com/api/v1/visualizations/42/regenerate/" \
  -H "Authorization: Token your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "async": true
  }'
```

**Example Response:**
```json
{
  "status": "generating",
  "task_id": "regenerate-abc123",
  "message": "Regenerating Similarity Heatmap in the background"
}
```

---

### 6. Delete Visualization

Delete a visualization. Only the creator or project owner can delete.

**Endpoint:** `DELETE /api/v1/visualizations/{id}/`

**Example Request:**
```bash
curl -X DELETE "https://your-domain.com/api/v1/visualizations/42/" \
  -H "Authorization: Token your-api-token"
```

**Example Response:**
```
HTTP 204 No Content
```

---

### 7. Check Task Status

Check the status of an async generation task.

**Endpoint:** `GET /api/v1/visualizations/task_status/?task_id={task_id}`

**Query Parameters:**
- `task_id` (required): The task ID returned from an async operation

**Example Request:**
```bash
curl -X GET "https://your-domain.com/api/v1/visualizations/task_status/?task_id=abc123-def456" \
  -H "Authorization: Token your-api-token"
```

**Example Response (Pending):**
```json
{
  "task_id": "abc123-def456",
  "status": "PENDING",
  "ready": false
}
```

**Example Response (Success):**
```json
{
  "task_id": "abc123-def456",
  "status": "SUCCESS",
  "ready": true,
  "result": {
    "status": "success",
    "visualization_id": 47,
    "message": "heatmap visualization generated successfully"
  }
}
```

**Example Response (Failure):**
```json
{
  "task_id": "abc123-def456",
  "status": "FAILURE",
  "ready": true,
  "error": "Insufficient data: Need at least 2 images"
}
```

---

## Configuration Options

### Heatmap Configuration

```json
{
  "colormap": "viridis",     // matplotlib colormap name
  "figsize": [12, 8],        // [width, height] or null for auto
  "dpi": 100,                // dots per inch (72-300)
  "show_values": false,      // display scores in cells
  "title": "Custom Title"    // override default title
}
```

**Available Colormaps:** `viridis`, `plasma`, `inferno`, `magma`, `coolwarm`, `RdYlBu`, `RdYlGn`

### Correlation Matrix Configuration

```json
{
  "colormap": "coolwarm",    // matplotlib colormap name
  "figsize": [10, 10],       // [width, height] or null for auto
  "dpi": 100,                // dots per inch (72-300)
  "show_values": true,       // display correlation coefficients
  "title": "Custom Title"    // override default title
}
```

### Image Grid Configuration

```json
{
  "cols": 3,                  // number of columns
  "max_images": 12,           // maximum images to display
  "prompt": "architecture",   // specific prompt to filter by (optional)
  "sort_by": "score",         // "score" or "name"
  "sort_order": "desc",       // "desc" or "asc"
  "dpi": 100,                 // dots per inch
  "title": "Custom Title"     // override default title
}
```

---

## Error Responses

### 400 Bad Request

Missing or invalid parameters.

```json
{
  "error": "analysis_id and viz_type are required"
}
```

### 403 Forbidden

Insufficient permissions.

```json
{
  "error": "You don't have permission to generate visualizations for this analysis"
}
```

### 404 Not Found

Resource doesn't exist.

```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error

Server error during generation.

```json
{
  "error": "Insufficient data: Need at least 2 images for correlation matrix"
}
```

---

## Status Codes

- `200 OK`: Request successful
- `201 Created`: Visualization created (sync)
- `202 Accepted`: Task queued (async)
- `204 No Content`: Deletion successful
- `400 Bad Request`: Invalid parameters
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Generation failed

---

## Example Workflows

### Workflow 1: Generate and Download

1. Generate visualization asynchronously:
```bash
curl -X POST "https://your-domain.com/api/v1/visualizations/" \
  -H "Authorization: Token your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": 7,
    "viz_type": "heatmap",
    "async": true
  }'
```

Response: `{"task_id": "abc123", "status": "generating"}`

2. Poll for completion:
```bash
curl -X GET "https://your-domain.com/api/v1/visualizations/task_status/?task_id=abc123" \
  -H "Authorization: Token your-token"
```

Response: `{"status": "SUCCESS", "ready": true, "result": {"visualization_id": 42}}`

3. Get visualization details:
```bash
curl -X GET "https://your-domain.com/api/v1/visualizations/42/" \
  -H "Authorization: Token your-token"
```

4. Download file from `download_url` field

### Workflow 2: Batch Generation

Generate all default visualizations at once:

```bash
curl -X POST "https://your-domain.com/api/v1/visualizations/generate_default/" \
  -H "Authorization: Token your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": 7,
    "async": false
  }'
```

Response contains all three visualizations in `created` array.

### Workflow 3: Custom Configuration

Generate heatmap with custom settings:

```bash
curl -X POST "https://your-domain.com/api/v1/visualizations/" \
  -H "Authorization: Token your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": 7,
    "viz_type": "heatmap",
    "config": {
      "colormap": "coolwarm",
      "dpi": 150,
      "show_values": true
    },
    "async": false
  }'
```

---

## Rate Limits

- Async requests: Unlimited (queued via Celery)
- Sync requests: Recommended limit of 5/minute per user
- Large datasets should use async generation

---

## Best Practices

1. **Use async for large datasets**: Datasets with >50 images should use async generation
2. **Poll task status**: Check every 2-5 seconds for async tasks
3. **Handle errors gracefully**: Generation can fail due to insufficient data
4. **Cache visualizations**: Visualizations don't auto-update, regenerate when data changes
5. **Use appropriate DPI**: 100 DPI for screen, 300 DPI for print
6. **Batch generation**: Use `generate_default` for initial visualization set

---

## Related Documentation

- [Phase 3 Visualization Plan](PHASE_3_VISUALIZATION_PLAN.md)
- [Generator Architecture](clip_web/apps/visualizations/generators/)
- [API Swagger Docs](https://your-domain.com/api/docs/)

---

**Last Updated**: November 5, 2025
**API Version**: v1
**Status**: Phase 3.3 Complete
