CREATE TABLE product_table (
    title VARCHAR(255),
    price VARCHAR(10),
    speed INT,
    glide INT,
    turn INT,
    fade INT,
    link_to_disc VARCHAR(255),
    image_url VARCHAR(255),
    store VARCHAR(255),
    PRIMARY KEY (title, store)
);