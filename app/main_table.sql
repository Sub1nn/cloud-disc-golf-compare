USE disc_golf_db;

CREATE TABLE product_table (
    title VARCHAR(255),
    price DECIMAL(10, 2),
    currency VARCHAR(5),
    speed DECIMAL(3, 1),
    glide DECIMAL(3, 1),
    turn DECIMAL(3, 1),
    fade DECIMAL(3, 1),
    link_to_disc VARCHAR(255),
    image_url VARCHAR(255),
    store VARCHAR(255),
    PRIMARY KEY (title, store)
);