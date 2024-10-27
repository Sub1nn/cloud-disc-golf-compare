// create a package from the source repository

data "archive_file" "function_dist" {
	type        = "zip"
	source_dir  = "./../${var.repository_name}"
	output_path = "./../${var.repository_name}.zip"
}

resource "google_storage_bucket_object" "object" {
	name = var.object_name
	bucket = var.bucket_name
	source = data.archive_file.function_dist.output_path
}

output "object_name" {
 	 value = google_storage_bucket_object.object.name
}

// create a app engine standard app

resource "google_app_engine_standard_app_version" "standard_app" {
  	version_id = var.version_id
	project = var.project
	service = var.service
	runtime = var.runtime
	
	entrypoint {
		shell = var.shell
	}

	deployment {
		zip {
			source_url = "https://storage.googleapis.com/${var.bucket_name}/${var.object_name}"
		}
	}

	# vpc_access_connector {

	# }

	env_variables = {
		port = var.port
	}

	instance_class = var.instance_class

	delete_service_on_destroy  = var.delete_service_on_destroy
	service_account = var.service_account
	depends_on = [resource.google_storage_bucket_object.object]
}