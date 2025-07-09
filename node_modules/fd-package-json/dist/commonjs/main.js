"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.findPackageSync = exports.findPackagePathSync = exports.findPackage = exports.findPackagePath = void 0;
const walk_up_path_1 = require("walk-up-path");
const node_path_1 = require("node:path");
const promises_1 = require("node:fs/promises");
const node_fs_1 = require("node:fs");
/**
 * Determines if a file exists or not
 * @param {string} path Path of the file
 * @return {Promise<boolean>}
 */
async function fileExists(path) {
    try {
        const stats = await (0, promises_1.stat)(path);
        return stats.isFile();
    }
    catch (_err) {
        return false;
    }
}
/**
 * Synchronously determines if a file exists or not
 * @param {string} path Path of the file
 * @return {boolean}
 */
function fileExistsSync(path) {
    try {
        const stats = (0, node_fs_1.statSync)(path);
        return stats.isFile();
    }
    catch (_err) {
        return false;
    }
}
/**
 * Finds the path of the first `package.json` encountered when traversing
 * the file system upwards from the specified `cwd`.
 * @param {string} cwd Current/starting directory
 * @return {Promise<string|null>}
 */
async function findPackagePath(cwd) {
    for (const path of (0, walk_up_path_1.walkUp)(cwd)) {
        const packagePath = (0, node_path_1.resolve)(path, 'package.json');
        const hasPackageJson = await fileExists(packagePath);
        if (hasPackageJson) {
            return packagePath;
        }
    }
    return null;
}
exports.findPackagePath = findPackagePath;
/**
 * Finds and returns the contents of the first `package.json` encountered
 * when traversing the file system upwards from the specified `cwd`.
 * @param {string} cwd Current/starting directory
 * @return {Promise<Package | null>}
 */
async function findPackage(cwd) {
    const packagePath = await findPackagePath(cwd);
    if (!packagePath) {
        return null;
    }
    try {
        const source = await (0, promises_1.readFile)(packagePath, { encoding: 'utf8' });
        return JSON.parse(source);
    }
    catch (_err) {
        return null;
    }
}
exports.findPackage = findPackage;
/**
 * Synchronously Finds the path of the first `package.json` encountered when
 * traversing the file system upwards from the specified `cwd`.
 * @param {string} cwd Current/starting directory
 * @return {string|null}
 */
function findPackagePathSync(cwd) {
    for (const path of (0, walk_up_path_1.walkUp)(cwd)) {
        const packagePath = (0, node_path_1.resolve)(path, 'package.json');
        const hasPackageJson = fileExistsSync(packagePath);
        if (hasPackageJson) {
            return packagePath;
        }
    }
    return null;
}
exports.findPackagePathSync = findPackagePathSync;
/**
 * Synchronously finds and returns the contents of the first `package.json`
 * encountered when traversing the file system upwards from the specified `cwd`.
 * @param {string} cwd Current/starting directory
 * @return {Package | null}
 */
function findPackageSync(cwd) {
    const packagePath = findPackagePathSync(cwd);
    if (!packagePath) {
        return null;
    }
    try {
        const source = (0, node_fs_1.readFileSync)(packagePath, { encoding: 'utf8' });
        return JSON.parse(source);
    }
    catch (_err) {
        return null;
    }
}
exports.findPackageSync = findPackageSync;
