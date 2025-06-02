import express from "express"
import {config} from "dotenv"
import { routes } from "./routes"
config()

const app = express(),
    port = process.env.PORT || 3000

app.use(express.json())
app.use(express.urlencoded({ extended: true }))
for (const route of routes) {
    console.log(`Registering route: ${route.path}`)
    app.use(route.path, route.router)
}

app.listen(port, () => {
    console.log(`Server is running on port ${port}`)
})