provider "google" {
    credentials = file(var.general_details.path_to_service_key)
    project = var.general_details.project_id
    region = var.general_details.region
}

module "enable_google_apis_for_app_engine" {
    source = "./modules/enable_google_apis"
    project = var.general_details.project_id
    services = var.enable_google_apis.services
}

module "create_service_account_for_app_engine" {
    source = "./modules/create_service_account"
    project = var.general_details.project_id
    service_account_display_name = var.appengine_service_account.service_account_display_name
	roles = var.appengine_service_account.service_account_roles
    depends_on = [module.enable_google_apis_for_app_engine]
}

module "create_storage_bucket" {
    source = "./modules/create_storage_bucket"
    bucket_name = var.appengine_bucket.bucket_name
    bucket_location = var.appengine_bucket.bucket_location
    depends_on = [module.enable_google_apis_for_app_engine]
}

module "app_engine_create_standard" {
    source = "./modules/app_engine_create_standard"

    for_each = {for version in var.appengine_versions : version.version_id => version} 

    // package the app

    repository_name = each.value.repository_name
    object_name = "${each.value.object_name}_${each.value.version_id}.zip"             
    bucket_name = module.create_storage_bucket.bucket_name

    // launch app engine

    version_id = each.value.version_id
    service = each.value.service
    project = var.general_details.project_id
    runtime = each.value.runtime
    shell = each.value.shell
    port = each.value.port
    db_pwd = each.value.db_pwd
    instance_class = each.value.instance_class
    delete_service_on_destroy = each.value.delete_service_on_destroy
    service_account = module.create_service_account_for_app_engine.service_account_email

    depends_on = [module.enable_google_apis_for_app_engine, module.create_service_account_for_app_engine, module.create_storage_bucket]
}