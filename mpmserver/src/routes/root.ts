import { Route } from "../type/Route";
import { version } from "../../package.json";
import { Router } from "express";

const router = Router()

router.get("/", (req, res) => {
    res.status(200).json({
        message: "Welcome to Multiplaymat ! (°◓°)",
        version,
    })
})

export const root = {
    path: "/",
    router
} as Route