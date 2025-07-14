# Sentinel Commander

> ⚠️ **Early Alpha Notice**  
> Sentinel Commander is currently in early alpha. While many core features are functional and actively used, the platform is under continuous development. Expect rapid iteration, breaking changes, and new modules arriving frequently.

---

## Notice
I am still trying to figure out what Sentinel Commander is going to be, and what is the best way to build such an application.
There will be many iterations before I land on something which I am happy with.

## Module Exclusions
Due to the development overhead of having to much at one time, I am going to focus on the core functionality, and add all other things as modules.

## Backend
There are many things that needs to be reworked on the backend. The change from a pure SQLite to Postgres has improved the performance a lot, 
now the next step would be to add some kind of memory key value store, and a message queue.