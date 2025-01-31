# Keycloak

**Primer to Keycloak**

Keycloak is an open-source Identity and Access Management (IAM) solution aimed at modern applications and services. It provides features such as single sign-on (SSO), user federation, social login, and identity brokering to simplify and secure authentication and authorization processes in your application ecosystem.

### **Key Features**
1. **Single Sign-On (SSO):**
   - Users can log in once and gain access to multiple applications without needing to authenticate repeatedly.
   - Supports session management and token revocation.

2. **Identity Federation:**
   - Integrates with external identity providers like LDAP (e.g., Active Directory) and social logins (e.g., Google, Facebook).

3. **OAuth2 and OpenID Connect (OIDC):**
   - Supports industry-standard protocols for secure access delegation and authentication.

4. **Access Control:**
   - Offers role-based and fine-grained access control using Authorization Services.
   - Policies can be configured using Keycloak's admin console.

5. **User Management:**
   - Built-in user registration, password reset, and account management capabilities.

6. **Extensibility:**
   - Extend functionality with custom themes, user workflows, and providers (e.g., authenticators, protocols, mappers).

7. **Admin Console:**
   - A powerful graphical interface for managing realms, clients, roles, and users.

8. **High Availability:**
   - Can be deployed in a clustered environment for scalability and resilience.

### **Key Concepts**
1. **Realm:**
   - A realm is an isolated tenant within a Keycloak instance. Each realm can manage its own users, credentials, and clients.
   - Example: A company might have separate realms for development, testing, and production environments.

2. **Client:**
   - A client represents an application or service that wants to use Keycloak for authentication. Clients can be frontend apps, backend services, or APIs.
   - Example: A web app, a mobile app, or an API.

3. **User:**
   - Represents the end-user accessing the system. Users can be managed internally by Keycloak or federated via external identity providers.

4. **Roles:**
   - Define access permissions for users and groups. Roles can be assigned globally (realm roles) or to specific clients (client roles).

5. **Groups:**
   - Used to organize users and assign roles collectively.

6. **Identity Provider (IdP):**
   - An external system that authenticates users. Keycloak supports IdPs like SAML, LDAP, and social login providers.

7. **Authentication Flows:**
   - Define how users authenticate, including multi-factor authentication (MFA), passwordless login, and custom authentication mechanisms.

### **Protocols Supported**
1. **OpenID Connect (OIDC):**
   - A simple identity layer on top of OAuth2.
   - Commonly used for web and mobile applications.

2. **OAuth2:**
   - Authorization framework that allows third-party applications to access resources on behalf of a user.

3. **SAML 2.0:**
   - Security Assertion Markup Language for single sign-on (SSO).

### **How Keycloak Works**
1. **User Authentication:**
   - A user tries to access a protected resource in a client application.
   - The client redirects the user to Keycloak's login page.
   - Keycloak authenticates the user (via username/password, MFA, or external IdP).
   - If successful, Keycloak issues an access token, ID token, and optionally a refresh token.

2. **Authorization:**
   - Based on the roles and permissions, Keycloak determines what resources the user can access.

3. **Token Validation:**
   - Client applications validate tokens using Keycloak’s public key.

### **Deployment Options**
1. **Standalone Mode:**
   - Run Keycloak on a single server or container.
   - Suitable for small-scale applications or development.

2. **Clustered Mode:**
   - Deploy Keycloak in a distributed setup for high availability and scalability.

3. **Containerized Deployment:**
   - Keycloak provides Docker images for easy containerized deployments.

4. **Cloud Deployment:**
   - Can be deployed on cloud providers like AWS, Azure, or Google Cloud using Kubernetes or managed services.

### **Keycloak Use Case Examples**
1. **Enterprise SSO:**
   - Integrate Keycloak with internal enterprise applications for centralized user authentication.

2. **API Security:**
   - Secure APIs using Keycloak-issued OAuth2 tokens.

3. **Social Login:**
   - Enable login via social providers like Google or Facebook without implementing them yourself.

4. **Customer IAM:**
   - Use Keycloak to manage customer identities for a SaaS application.

5. **Federated Identity:**
   - Connect to external IdPs like LDAP or Active Directory.

### **Getting Started**
1. **Install Keycloak:**
   - Use Docker:  
     ```bash
     docker run -p 8080:8080 -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:latest start-dev
     ```
   - Alternatively, download and install from the [Keycloak website](https://www.keycloak.org).

2. **Access Admin Console:**
   - Open `http://localhost:8080` in your browser and log in using the admin credentials (`admin/admin`)

3. **Create a Realm:**
   - Add a new realm for your application.

4. **Register Clients:**
   - Add client applications to the realm, specifying their protocol (OIDC/SAML) and configuration.

5. **Add Users:**
   - Create users and assign roles for testing.

6. **Integrate with Applications:**
   - Configure your app to use Keycloak for authentication by providing the realm and client settings.

Keycloak is a powerful and flexible IAM solution that fits a variety of use cases. With proper configuration and integration, it can significantly enhance the security and user experience of your applications.

---
# Keycloak: First Time Usage
> https://www.keycloak.org/getting-started/getting-started-kube

- Create a Realm
- Create a User
- Log in to Account Console -> opened URL to get to it (lots of UI clicks otherwise) - `http://localhost:8080/realms/myrealm/account`
- Secure first application
  - create client for OpenID Connect
  - use SPA testing application to validate client (after setting web origin as `https://www.keycloak.org`)

# Keycloak: Practical Example
Production-level Keycloak deployment with:
- Certificate Manager
- Sealed Secrets
- PostgreSQL HA (high-availability variant)

NOTE: This simply runs commands from an online developer's custom Docker Image with additional utilities called [miniDevOps](https://github.com/brakmic/miniDevOps?tab=readme-ov-file)
- ```
  docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock --network=host -v ./session:/session -p 443:443 brakmic/devops:latest
  ```
- ssh into container
- ```
  # Kind - create new cluster + Ingress-Controller
  sudo ./create_cluster
  k get po -A  # list pods
  k get deploy -A  # list deployments

  # install Keycloak via Script (uses Helm)
  cd /session/work/yamls
  sudo ../scripts/run_kc_system.sh
  ```