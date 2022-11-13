Architecture: MAS Core
===============================================================================

- [Controller Managers](#controller-managers)
- [Entity Managers](#entity-managers)
- [Suite Administration Services](#suite-administration-services)
- [Identity Provider Service](#identity-provider-service)
- [Catalog Management Services](#catalog-management-services)
- [User Registry](#user-registry)
- [Console](#console)
- [Licensing and Usage Data Collection](#licensing-and-usage-data-collection)

Controller Managers
-------------------------------------------------------------------------------
### ibm-mas-operator
Watches `Suite.core.mas.ibm.com`.

Primary controller manager for an installation of the MAS core services.

### ibm-truststore-mgr-controller-manager
Watches `Truststore.ibm-truststore-mgr.ibm.com`.

Truststores pod is the operator responsible for handling the trust store request and add provided truststore in the format consumed by the servers.


Entity Managers
-------------------------------------------------------------------------------
### entitymgr-addons
Add-ons configuration

### entitymgr-bascfg
Watches `BASCfg.config.mas.ibm.com`.

Entity Manager used to manage UDS integration with MAS. Generating internal certificates, performing configuration verification and all deployment of all UDS related pods.

### entitymgr-coreidp
Watches `CoreIDP.internal.mas.ibm.com`.

Entity Manager used to manage Coreidp integration with MAS. Generating internal certificates, validations, coreidp-login and coreidp PODs deployment.

### entitymgr-idpcfg
Watches `IDPCfg.config.mas.ibm.com`.

Entity Manager used to manage IDP integration with MAS. Generating internal certificates, performing configuration and verification.

### entitymgr-jdbccfg
Watches `JDBCCfg.config.mas.ibm.com`.

Entity Manager used to manage JDBC integration with MAS, performing configuration validation.

### entitymgr-kafkacfg
Watches `KafkaCfg.config.mas.ibm.com`.

Entity Manager used to manage Kafka integration with MAS, performing configuration validation.

### entitymgr-jdbccfg
Watches `MongoCfg.config.mas.ibm.com`.

Entity Manager used to manage Mongo integration with MAS, performing configuration validation.

### entitymgr-objectstorage
Watches `ObjectStorageCfg.config.mas.ibm.com`.

Entity Manager used to manage ObjectStorage integration with MAS, performing configuration validation.

### entitymgr-pushnotificationcfg
Watches `PushNotificationCfg.config.mas.ibm.com`.

Entity Manager used to manage PushNotification integration with MAS, performing configuration validation.

### entitymgr-scimcfg
Watches `SCIMCfg.config.mas.ibm.com`.

Entity Manager used to manage SCIM (LDAP User Sync) integration with MAS, performing configuration validation and resources creation such as scimsync-agent job and scimsync liberty pod.

### entitymgr-slscfg
Watches `SLSCfg.config.mas.ibm.com`.

Entity Manager used to manage SLS integration with MAS, performing configuration validation and resources creation such as licensing-mediator pod. This pod is also responsible to register the SLS client in the SLS server.

### entitymgr-smtpcfg
Watches `SMTPCfg.config.mas.ibm.com`.

Entity Manager used to manage SMTP integration with MAS, performing configuration validation.

### entitymgr-watsonstudiocfg
Watches `WatsonStudioCfg.config.mas.ibm.com`.

Entity Manager used to manage Watson Studio integration with MAS, performing configuration validation.

### entitymgr-ws
Watches `Workspace.core.mas.ibm.com`.

Entity Manager used to manage Workspace creation in MAS.


Suite Administration Services
-------------------------------------------------------------------------------
### coreapi
The MAS CoreAPI pod which provides a HTTPS APIs to support working with Kubernetes resources natively. It primarily acts as a proxy to the Kubernetes APIs and MongoDB integration.

Route: `https://api.{masdomain}`

#### Deployment Topology
![](img/coreapi.png)

### internalapi
The internal api pod which provides the Internal version of the MAS Administrative API, for example, user management. Notes, this is used by internal components only. Application to application communication.

#### Deployment Topology
![](img/internalapi.png)

### mobileapi
The mobile API pods which provides the mobile application package API and specifically it serves up the navigator application package. It integrates with coreapi.

#### Deployment Topology
![](img/mobileapi.png)

### monagent-mas
Monagent is responsible to monitor MAS general components health and report back to Suite CR.

### pushnotification
Push notification support is an optional extension to the core API that can be configured by a system administrator, it allows the user to enable push notification support across MAS applications.

!!! info
    The push notification service is available at **https://api.{{domain}}/pushnotification** only if the system scope **PushNotificationCfg** resource has been created by the administrator.

#### Deployment Topology
![](img/pushnotify.png)



Identity Provider Service
-------------------------------------------------------------------------------
### coreidp
The coreidp pod is a Liberty based server which handles the authentication, access management and user privileges authorization managed by Maximo Application Suite. This pod will integrate with internal applications through OIDC flow and externally using SAML.

### coreidp-login
The coreidp login pods which hosts login page and superuser login logic for Maximo Application Suite.  This is not meant to be a MAS endpoint but used as part of the redirect during MAS authentication flow.

Route: `https://auth.{masdomain}`


Catalog Management Services
-------------------------------------------------------------------------------
The MAS Catalog acts as the mechanism for customers to discover the resources in MAS that they are interested in, it allows us to abstract the actual resource (ie implementation) of a capability away from how it is presented as a catalog item.

### catalogapi
The catalogapi pod which provides read access to the catalog inventory.  The catalog API is exposed via endpoints in [Core API](#coreapi) which proxy requests to the internal catalog API service.

### catalogmgr
The catalogapi pod which provides inventory management and AppPoint reservation APIs.

![](img/catalog.png)


User Registry
-------------------------------------------------------------------------------
### groupsync-coordinator
The group sync manager pod which coordinates the group sync activities between MAS and Applications

### usersync-coordinator
The user sync manager pod which coordinates the user sync activities between MAS and Applications

#### Deployment Topology
![](img/usersync.png)


Console
-------------------------------------------------------------------------------
### admin-dashboard
MAS Core Admin dashboard UI pod which is user interface for Maximo Application Suite administrator including system admin work and user management.

Route: `https://admin.{masdomain}`

### homepage
MAS Core homepage UI pod. This is main page when you are not running in a workspace-based endpoint.

Route: `https://home.{masdomain}`

### navigator
The Application Navigator is a workspace-based UI acting as a home page where users can access any application.

Route: `https://{workspace}.home.{masdomain}`


Licensing and Usage Data Collection
-------------------------------------------------------------------------------
### accapppoints
The accapppoints reporter pod which pulls data from SLS, converts app point reports to Account Contractual Usage events and license usage reports to Account Adoption Usage events, and pushes the events to UDS every hour.

### adoptionusageapi
AdoptionUsage API is the api which enables this process by providing the API which is invoked by coreapi to share information about user when they login to any application.

### adoptionusage-reporter
The adoptionusage reporter pulls the data related to adoption of different applications by users. It gathers data in terms of number of users and total AppPoints of these users who login to each of the MAS applications, whenever the users login to these applications. This application runs as a cronjob and sends this data to UDS ( User Data Services). (earlier known as BAS - Behaviour Analytics Services). UDS in turn sends this data to IBM growth stack including Segment and Amplitude where different IBM roles like Product management/ Operations etc can understand adoption patterns of different MAS applications by using relevant dashboards.

### licensing-mediator
SLS mediator is a bridge between MAS and SLS. It proxies a subset of the SLS APIs, hosts internal APIs that manage licenses for user entitlement and SSO flows, and periodically runs a licensing sync process that ensures the MAS user registry and user licenses in SLS are in sync.

#### Deployment Topology
![](img/slsmediator.png)

### milestonesapi
The milestones API is responsible for reporting critical user events, known as “milestones”, to Behaviour Analytics Service or “BAS”. BAS forwards these events into the IBM Growth Stack, which includes tools to help IBM gain insight into customer usage and assist with campaign administration.

#### Deployment Topology
![](img/milestonesapi.png)
