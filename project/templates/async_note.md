# How to Async heavy requests

> **Parler à ulysse de découplage**
## Current state of things
Problem : timeouts everywhere

```mermaid
sequenceDiagram
    loop browser is loading
    USER->>+BROWSER: Request addition
    BROWSER->>+SERVER: Post form data
    SERVER-->>APIS: Request data
    APIS -->>SERVER: Return data
    SERVER->>-BROWSER: Return results
    BROWSER->>-USER: shows results
    end
```

---

## The FrontEnd approach

- Biblio
  - JS redirect : `window.location.href = "http://www.w3schools.com";`
  - [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)


- Pros:
    - No more timeout from browser
- Limits:
  - Change nothing in the fact that the requests are way too long, and can timeout at any other point (heroku....)

```mermaid
sequenceDiagram
    loop browser is loading
    USER->>+BROWSER: Request addition async
    BROWSER->>-USER: Show loading state in page
    end
    loop JS Waits
    BROWSER->>+SERVER: Post form data
    SERVER-->>APIS: Request data
    APIS -->> SERVER: Return data
    SERVER->>-BROWSER: Return link to a new page
    end
    BROWSER->>USER: Redirect to the new link
```


Basic fetch request

```javascript
fetch('http://example.com/movies.json')
  .then(response => response.json())
  .then(data => console.log(data));
```
