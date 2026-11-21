FROM php:8.2-apache

# Install PDO MySQL extension
RUN docker-php-ext-install pdo pdo_mysql

# Enable Apache mod_rewrite
RUN a2enmod rewrite

# Copy backend files
COPY . /var/www/html/

# Set permissions
RUN chown -R www-data:www-data /var/www/html/

# Configure Apache DocumentRoot to point to where the api is if needed, 
# but assuming index.php is inside api/v1/, the root works if properly structured.
EXPOSE 80
