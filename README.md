**Project name:** Disc Golf Equipment Price Comparator

**Summary (singular purpose):** The purpose of the project is to provide a central location for displaying the prices of different disc golf equipment based on data from manufacturers and resellers.

**Detailed description:**

Disc golf, also called frisbee golf, is a rapidly growing sport in the United States, Finland, and Estonia. Here is some insight into the sport:

* https://en.wikipedia.org/wiki/Disc_golf
* https://www.dgpt.com/
* https://www.youtube.com/@JomezPro

Given the growth in the sport, there are currently multiple disc golf equipment manufacturers, such as Discmania, Innova, Dynamic Discs, Latitude 64, and many others, as well as an even wider variety of disc golf equipment resellers. The numerous options can often make it difficult to find the best market deals. Therefore, the idea behind my course project is to compile shop data from both resellers and manufacturers, and aggregate the data into a central location. As mentioned, this aims to help identify the most competitively priced products in the market and even discover unique editions of equipment that are sold exclusively in certain stores. Some of the manufacturer and reseller sites included are listed below, primarily focusing on a scope local to the Nordics and Baltics:

* par3.lv
* discsporteurope.com
* powergrip.fi
* diskiundiskicesis.lv
* latitude64.com
* kiekkokingi.fi

This will enables site visitors to easily search, filter, and compare products between the resellers to make the best choice.

**To access the project, please visit the following site: https://gardsgids.com/**

From a technical and architectural perspective, the process is as follows:

* The product information from different sources is collected by executing the perform_data_update.py file, which will execute functions to read data from different stores, normalize it, and store it in a MySQL database hosted on Google Cloud.
* Then, in main.py, the data is read and rendered into the front-end using templating and Flask, a web application library. The front-end utilizes HTML, CSS, and JavaScript embedded within the HTML.
* For deploying the web application to the internet, a Google Cloud native service called Google App Engine is used. With the help of Terraform, all necessary Google App Engine accesses and related services are set up. Terraform can also automatically deploy a new version of the web application based on the latest version in the repository to the Google App Engine. All service configurations and web application deployment settings are defined in the example_configuration.json file, which is used to populate the Terraform modules.