// create service account and grant roles to it

resource "google_service_account" "custom_service_account" {
    account_id = var.project
    display_name = var.service_account_display_name
}

resource "google_project_iam_member" "service_account_roles" {  
    for_each = toset(var.roles)
    project = google_service_account.custom_service_account.account_id
    role = each.value
    member = "serviceAccount:${google_service_account.custom_service_account.email}"
    depends_on = [resource.google_service_account.custom_service_account]
}