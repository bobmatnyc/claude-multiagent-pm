import { type Context } from 'conventional-changelog-writer';
import type { Logger, HostedGitInfo, Params, Commit } from './types.js';
export declare function getHostOptions(repository: Partial<HostedGitInfo> | null | undefined, context: Context | null | undefined): import("./types.js").HostOptions | null;
export declare function guessNextTag(previousTag: string, version?: string): string;
export declare function isUnreleasedVersion(semverTags: string[], version: string | undefined): boolean | "" | undefined;
export declare const versionTagRegex: RegExp;
export declare const defaultVersionRegex: RegExp;
export declare function defaultCommitTransform(commit: Commit, params: Params): Partial<Commit>;
export declare function bindLogNamespace(namespace: string, log: Logger): (messages: string | string[]) => void;
//# sourceMappingURL=utils.d.ts.map