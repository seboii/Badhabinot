package com.badhabinot.backend.config.persistence;

import com.zaxxer.hikari.HikariDataSource;
import jakarta.persistence.EntityManagerFactory;
import java.util.HashMap;
import java.util.Map;
import javax.sql.DataSource;
import org.flywaydb.core.Flyway;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.flyway.FlywayMigrationInitializer;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.boot.autoconfigure.orm.jpa.HibernateProperties;
import org.springframework.boot.autoconfigure.orm.jpa.JpaProperties;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.DependsOn;
import org.springframework.context.annotation.Primary;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.orm.jpa.JpaTransactionManager;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.PlatformTransactionManager;

@Configuration
public class MultiDataSourceConfiguration {

    private final JpaProperties jpaProperties;
    private final HibernateProperties hibernateProperties;

    public MultiDataSourceConfiguration(JpaProperties jpaProperties, HibernateProperties hibernateProperties) {
        this.jpaProperties = jpaProperties;
        this.hibernateProperties = hibernateProperties;
    }

    @Bean
    @Primary
    @ConfigurationProperties("app.datasource.auth")
    public DataSourceProperties authDataSourceProperties() {
        return new DataSourceProperties();
    }

    @Bean
    @Primary
    public DataSource authDataSource(@Qualifier("authDataSourceProperties") DataSourceProperties properties) {
        return properties.initializeDataSourceBuilder().type(HikariDataSource.class).build();
    }

    @Bean
    @ConfigurationProperties("app.datasource.user")
    public DataSourceProperties userDataSourceProperties() {
        return new DataSourceProperties();
    }

    @Bean
    public DataSource userDataSource(@Qualifier("userDataSourceProperties") DataSourceProperties properties) {
        return properties.initializeDataSourceBuilder().type(HikariDataSource.class).build();
    }

    @Bean
    @ConfigurationProperties("app.datasource.monitoring")
    public DataSourceProperties monitoringDataSourceProperties() {
        return new DataSourceProperties();
    }

    @Bean
    public DataSource monitoringDataSource(@Qualifier("monitoringDataSourceProperties") DataSourceProperties properties) {
        return properties.initializeDataSourceBuilder().type(HikariDataSource.class).build();
    }

    @Bean
    public Flyway authFlyway(@Qualifier("authDataSource") DataSource dataSource) {
        return Flyway.configure().dataSource(dataSource).locations("classpath:db/auth").load();
    }

    @Bean
    public FlywayMigrationInitializer authFlywayInitializer(@Qualifier("authFlyway") Flyway flyway) {
        return new FlywayMigrationInitializer(flyway);
    }

    @Bean
    public Flyway userFlyway(@Qualifier("userDataSource") DataSource dataSource) {
        return Flyway.configure().dataSource(dataSource).locations("classpath:db/user").load();
    }

    @Bean
    public FlywayMigrationInitializer userFlywayInitializer(@Qualifier("userFlyway") Flyway flyway) {
        return new FlywayMigrationInitializer(flyway);
    }

    @Bean
    public Flyway monitoringFlyway(@Qualifier("monitoringDataSource") DataSource dataSource) {
        return Flyway.configure().dataSource(dataSource).locations("classpath:db/monitoring").load();
    }

    @Bean
    public FlywayMigrationInitializer monitoringFlywayInitializer(@Qualifier("monitoringFlyway") Flyway flyway) {
        return new FlywayMigrationInitializer(flyway);
    }

    @Bean(name = "authEntityManagerFactory")
    @Primary
    @DependsOn("authFlywayInitializer")
    public LocalContainerEntityManagerFactoryBean authEntityManagerFactory(@Qualifier("authDataSource") DataSource dataSource) {
        return entityManagerFactory(dataSource, "com.badhabinot.backend.model.auth", "auth");
    }

    @Bean(name = "userEntityManagerFactory")
    @DependsOn("userFlywayInitializer")
    public LocalContainerEntityManagerFactoryBean userEntityManagerFactory(@Qualifier("userDataSource") DataSource dataSource) {
        return entityManagerFactory(dataSource, "com.badhabinot.backend.model.user", "user");
    }

    @Bean(name = "monitoringEntityManagerFactory")
    @DependsOn("monitoringFlywayInitializer")
    public LocalContainerEntityManagerFactoryBean monitoringEntityManagerFactory(@Qualifier("monitoringDataSource") DataSource dataSource) {
        return entityManagerFactory(dataSource, "com.badhabinot.backend.model.monitoring", "monitoring");
    }

    @Bean(name = "authTransactionManager")
    @Primary
    public PlatformTransactionManager authTransactionManager(@Qualifier("authEntityManagerFactory") EntityManagerFactory entityManagerFactory) {
        return new JpaTransactionManager(entityManagerFactory);
    }

    @Bean(name = "userTransactionManager")
    public PlatformTransactionManager userTransactionManager(@Qualifier("userEntityManagerFactory") EntityManagerFactory entityManagerFactory) {
        return new JpaTransactionManager(entityManagerFactory);
    }

    @Bean(name = "monitoringTransactionManager")
    public PlatformTransactionManager monitoringTransactionManager(@Qualifier("monitoringEntityManagerFactory") EntityManagerFactory entityManagerFactory) {
        return new JpaTransactionManager(entityManagerFactory);
    }

    private LocalContainerEntityManagerFactoryBean entityManagerFactory(
            DataSource dataSource,
            String packagesToScan,
            String persistenceUnit
    ) {
        LocalContainerEntityManagerFactoryBean entityManagerFactory = new LocalContainerEntityManagerFactoryBean();
        entityManagerFactory.setDataSource(dataSource);
        entityManagerFactory.setPackagesToScan(packagesToScan);
        entityManagerFactory.setPersistenceUnitName(persistenceUnit);
        entityManagerFactory.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        entityManagerFactory.setJpaPropertyMap(determineHibernateProperties());
        return entityManagerFactory;
    }

    private Map<String, Object> determineHibernateProperties() {
        Map<String, Object> properties = new HashMap<>(
                hibernateProperties.determineHibernateProperties(jpaProperties.getProperties(), new org.springframework.boot.autoconfigure.orm.jpa.HibernateSettings())
        );
        properties.putIfAbsent("hibernate.hbm2ddl.auto", "validate");
        return properties;
    }

    @Configuration
    @EnableJpaRepositories(
            basePackages = "com.badhabinot.backend.repository.auth",
            entityManagerFactoryRef = "authEntityManagerFactory",
            transactionManagerRef = "authTransactionManager"
    )
    static class AuthJpaConfiguration {
    }

    @Configuration
    @EnableJpaRepositories(
            basePackages = "com.badhabinot.backend.repository.user",
            entityManagerFactoryRef = "userEntityManagerFactory",
            transactionManagerRef = "userTransactionManager"
    )
    static class UserJpaConfiguration {
    }

    @Configuration
    @EnableJpaRepositories(
            basePackages = "com.badhabinot.backend.repository.monitoring",
            entityManagerFactoryRef = "monitoringEntityManagerFactory",
            transactionManagerRef = "monitoringTransactionManager"
    )
    static class MonitoringJpaConfiguration {
    }
}
