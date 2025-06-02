import { RequestHandler } from "express";

export type Route = {
    path: string;
    router: RequestHandler
}