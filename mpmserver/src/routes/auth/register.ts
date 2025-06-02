import { Router, Request, Response } from "express";
import db from "../../db";
import { Route } from "../../type/Route";
import { createHmac } from "crypto";

const router = Router();

router.post("/", async (req: Request, res: Response): Promise<void> => {
    const { username, password, email } = req.body;
    if (!username || !password || !email) {
        res.status(400).json({ error: "Username, email and password are required." });
        return;
    }
    try {
        const existingUser = await db.user.findUnique({ where: { name: username } });
        if (existingUser) {
            res.status(409).json({ error: "Username already exists." });
            return;
        }

        const newUser = await db.user.create({ data: {
            name: username,
            password: createHmac('sha256', process.env.HASH_SALT as string).update(password).digest('hex'),
            email
        } });
        res.status(201).json({ message: "User registered successfully.", user: newUser });
    } catch (error) {
        console.error("Registration error:", error);
        res.status(500).json({ error: "Internal server error." });
    }
});

export const register = {
    path: "/auth/register",
    router
} as Route