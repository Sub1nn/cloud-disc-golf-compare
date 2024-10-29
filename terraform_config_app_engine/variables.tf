variable "general_details" {
    type = object({
        path_to_service_key = string
        project_id = string
        region = string
    })
}

variable "enable_google_apis" {
	type = object({
		services = list(string)
	})
}

variable "appengine_service_account" {
	type = object({
		service_account_display_name = string
		service_account_roles = list(string)
	})
}

variable "appengine_bucket" {
    type = object({
        bucket_name = string
        bucket_location = string
    })
}

variable "appengine_versions" {
    type = list(object({
        version_id = string
        repository_name = string
        service = string
        object_name = string
        runtime = string
        shell = string
        port = string
        db_pwd = string
        instance_class  = string
        delete_service_on_destroy = bool
    }))
}