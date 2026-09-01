@description('Primary location for all resources')
param location string = resourceGroup().location

@description('Unique environment suffix')
param environmentName string = 'prod'

@description('PostgreSQL administrator login')
param dbAdminUser string = 'shivi_admin'

@secure()
@description('PostgreSQL administrator password')
param dbAdminPassword string

// 1. Log Analytics Workspace for Observability
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-shivi-${environmentName}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// 2. Azure Container Apps Managed Environment
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-shivi-${environmentName}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    zoneRedundant: true
  }
}

// 3. Azure Database for PostgreSQL Flexible Server (HA Enabled)
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: 'psql-shivi-${environmentName}'
  location: location
  sku: {
    name: 'Standard_D2ds_v5'
    tier: 'GeneralPurpose'
  }
  properties: {
    version: '16'
    administratorLogin: dbAdminUser
    administratorLoginPassword: dbAdminPassword
    highAvailability: {
      mode: 'ZoneRedundant'
    }
    storage: {
      storageSizeGB: 128
      autoGrow: 'Enabled'
    }
    backup: {
      backupRetentionDays: 30
      geoRedundantBackup: 'Enabled'
    }
  }
}

// 4. Azure Blob Storage for Cryptographic Evidence
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'stshivi${environmentName}'
  location: location
  sku: {
    name: 'Standard_ZRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// 5. Azure Service Bus for Decoupled Ingestion & Webhooks
resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: 'sb-shivi-${environmentName}'
  location: location
  sku: {
    name: 'Standard'
  }
}

// 6. Core Operations API Container App
resource coreApiApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'app-shivi-core-api'
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'core-api'
          image: 'shivi/core-api:latest'
          resources: {
            cpu: json('1.0')
            memory: '2.0Gi'
          }
          env: [
            {
              name: 'DATABASE_URL'
              value: 'postgresql+asyncpg://${dbAdminUser}:${dbAdminPassword}@${postgresServer.properties.fullyQualifiedDomainName}:5432/shivi_db?sslmode=require'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 2
        maxReplicas: 20
      }
    }
  }
}

output coreApiFqdn string = coreApiApp.properties.configuration.ingress.fqdn
