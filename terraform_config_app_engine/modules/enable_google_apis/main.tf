// enable apis

resource "google_project_service" "appengine_enable_api" {
    for_each = toset(var.services)
    project = var.project
    service = each.value
}