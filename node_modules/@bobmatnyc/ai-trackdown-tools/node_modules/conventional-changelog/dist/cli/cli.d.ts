#!/usr/bin/env node
import { type ConventionalChangelog } from '../index.js';
export interface Flags {
    infile?: string;
    outfile?: string;
    stdout?: boolean;
    preset?: string;
    pkg?: string;
    append?: boolean;
    releaseCount?: number;
    skipUnstable?: boolean;
    outputUnreleased?: boolean;
    verbose?: boolean;
    config?: string;
    context?: string;
    firstRelease?: boolean;
    lernaPackage?: string;
    tagPrefix?: string;
}
export declare const flags: {
    readonly infile: {
        readonly shortFlag: "i";
        readonly default: "CHANGELOG.md";
        readonly type: "string";
    };
    readonly outfile: {
        readonly shortFlag: "o";
        readonly type: "string";
    };
    readonly stdout: {
        readonly type: "boolean";
    };
    readonly preset: {
        readonly shortFlag: "p";
        readonly type: "string";
    };
    readonly pkg: {
        readonly shortFlag: "k";
        readonly type: "string";
    };
    readonly append: {
        readonly shortFlag: "a";
        readonly type: "boolean";
    };
    readonly releaseCount: {
        readonly shortFlag: "r";
        readonly type: "number";
    };
    readonly skipUnstable: {
        readonly type: "boolean";
    };
    readonly outputUnreleased: {
        readonly shortFlag: "u";
        readonly type: "boolean";
    };
    readonly verbose: {
        readonly shortFlag: "v";
        readonly type: "boolean";
    };
    readonly config: {
        readonly shortFlag: "n";
        readonly type: "string";
    };
    readonly context: {
        readonly shortFlag: "c";
        readonly type: "string";
    };
    readonly firstRelease: {
        readonly shortFlag: "f";
        readonly type: "boolean";
    };
    readonly lernaPackage: {
        readonly shortFlag: "l";
        readonly type: "string";
    };
    readonly tagPrefix: {
        readonly shortFlag: "t";
        readonly type: "string";
    };
};
export declare function runProgram(generator: ConventionalChangelog, flags: Flags): Promise<void>;
//# sourceMappingURL=cli.d.ts.map