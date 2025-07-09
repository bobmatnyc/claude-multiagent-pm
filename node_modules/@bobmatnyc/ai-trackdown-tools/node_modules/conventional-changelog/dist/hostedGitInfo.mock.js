export const samples = [
    [
        'bitbucket:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket:user@foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket:user@foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket:user:password@foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket:user:password@foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket::password@foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket::password@foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket:user@foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket:user@foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket:user:password@foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket:user:password@foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket::password@foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'bitbucket::password@foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git@bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git@bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git@bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git@bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@bitbucket.org:foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@bitbucket.org:foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@bitbucket.org:foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@bitbucket.org:foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://bitbucket.org/foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://bitbucket.org/foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@bitbucket.org/foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@bitbucket.org/foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@bitbucket.org/foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@bitbucket.org/foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@bitbucket.org/foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@bitbucket.org/foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://bitbucket.org/foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://bitbucket.org/foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@bitbucket.org/foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@bitbucket.org/foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@bitbucket.org/foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@bitbucket.org/foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@bitbucket.org/foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@bitbucket.org/foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://bitbucket.org/foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://bitbucket.org/foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@bitbucket.org/foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@bitbucket.org/foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@bitbucket.org/foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@bitbucket.org/foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@bitbucket.org/foo/bar',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@bitbucket.org/foo/bar#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://bitbucket.org/foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://bitbucket.org/foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@bitbucket.org/foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@bitbucket.org/foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@bitbucket.org/foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@bitbucket.org/foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@bitbucket.org/foo/bar.git',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@bitbucket.org/foo/bar.git#branch',
        {
            type: 'bitbucket',
            url: 'https://bitbucket.org/foo/bar/src/branch',
            host: 'https://bitbucket.org',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'foo/bar#sf1312sas',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/sf1312sas',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'foo/bar.git#sf1312sas',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/sf1312sas',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:user@foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:user@foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:user:password@foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:user:password@foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github::password@foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github::password@foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:user@foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:user@foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:user:password@foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github:user:password@foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github::password@foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'github::password@foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://user@github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://user@github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://user:password@github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://user:password@github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://:password@github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://:password@github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://git@github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://git@github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://user:password@github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://user:password@github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://:password@github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git://:password@github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@github.com:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@github.com:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@github.com:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@github.com:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@github.com:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@github.com:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@github.com:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@github.com:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@github.com:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@github.com:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@github.com:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@github.com:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://github.com:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://github.com:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@github.com:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@github.com:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@github.com:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@github.com:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@github.com:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@github.com:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://github.com:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://github.com:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@github.com:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@github.com:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@github.com:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@github.com:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@github.com:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@github.com:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://github.com:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://github.com:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@github.com:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@github.com:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@github.com:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@github.com:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@github.com:foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@github.com:foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://github.com:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://github.com:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@github.com:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@github.com:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@github.com:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@github.com:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@github.com:foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@github.com:foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@github.com/foo/bar#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@github.com/foo/bar.git',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@github.com/foo/bar.git#asd123sad',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/asd123sad',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://www.github.com/foo/bar',
        {
            type: 'github',
            url: 'https://github.com/foo/bar',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'foo/bar#branch with space',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/branch%20with%20space',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'foo/bar#branch:with:colons',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/branch%3Awith%3Acolons',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://github.com/foo/bar/tree/branch',
        {
            type: 'github',
            url: 'https://github.com/foo/bar/tree/branch',
            host: 'https://github.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:user@foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:user@foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:user:password@foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:user:password@foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab::password@foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab::password@foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:user@foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:user@foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:user:password@foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:user:password@foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab::password@foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab::password@foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'gitlab:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab:user@foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab:user@foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab:user:password@foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab:user:password@foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab::password@foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab::password@foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab:user@foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab:user@foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab:user:password@foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab:user:password@foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab::password@foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'gitlab::password@foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'user@gitlab.com:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@gitlab.com:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@gitlab.com:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@gitlab.com:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@gitlab.com:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@gitlab.com:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@gitlab.com:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@gitlab.com:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@gitlab.com:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user:password@gitlab.com:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@gitlab.com:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        ':password@gitlab.com:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'user@gitlab.com:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'user@gitlab.com:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'user:password@gitlab.com:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'user:password@gitlab.com:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        ':password@gitlab.com:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        ':password@gitlab.com:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'user@gitlab.com:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'user@gitlab.com:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'user:password@gitlab.com:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'user:password@gitlab.com:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        ':password@gitlab.com:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        ':password@gitlab.com:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://gitlab.com:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://gitlab.com:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@gitlab.com:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@gitlab.com:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@gitlab.com:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@gitlab.com:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@gitlab.com:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@gitlab.com:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://gitlab.com:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://gitlab.com:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@gitlab.com:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user@gitlab.com:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@gitlab.com:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://user:password@gitlab.com:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@gitlab.com:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://:password@gitlab.com:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://gitlab.com:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://gitlab.com:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://user@gitlab.com:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://user@gitlab.com:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://user:password@gitlab.com:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://user:password@gitlab.com:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://:password@gitlab.com:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://:password@gitlab.com:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://gitlab.com:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://gitlab.com:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://user@gitlab.com:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://user@gitlab.com:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://user:password@gitlab.com:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://user:password@gitlab.com:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://:password@gitlab.com:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+ssh://:password@gitlab.com:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://gitlab.com:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://gitlab.com:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@gitlab.com:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@gitlab.com:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@gitlab.com:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@gitlab.com:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@gitlab.com:foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@gitlab.com:foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://gitlab.com:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://gitlab.com:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@gitlab.com:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user@gitlab.com:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@gitlab.com:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://user:password@gitlab.com:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@gitlab.com:foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://:password@gitlab.com:foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'ssh://gitlab.com:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://gitlab.com:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://user@gitlab.com:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://user@gitlab.com:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://user:password@gitlab.com:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://user:password@gitlab.com:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://:password@gitlab.com:foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://:password@gitlab.com:foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://gitlab.com:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://gitlab.com:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://user@gitlab.com:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://user@gitlab.com:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://user:password@gitlab.com:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://user:password@gitlab.com:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://:password@gitlab.com:foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'ssh://:password@gitlab.com:foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://gitlab.com/foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://gitlab.com/foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@gitlab.com/foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@gitlab.com/foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@gitlab.com/foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@gitlab.com/foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@gitlab.com/foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@gitlab.com/foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://gitlab.com/foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://gitlab.com/foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@gitlab.com/foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user@gitlab.com/foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@gitlab.com/foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://user:password@gitlab.com/foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@gitlab.com/foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://:password@gitlab.com/foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git+https://gitlab.com/foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://gitlab.com/foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://user@gitlab.com/foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://user@gitlab.com/foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://user:password@gitlab.com/foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://user:password@gitlab.com/foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://:password@gitlab.com/foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://:password@gitlab.com/foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://gitlab.com/foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://gitlab.com/foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://user@gitlab.com/foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://user@gitlab.com/foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://user:password@gitlab.com/foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://user:password@gitlab.com/foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://:password@gitlab.com/foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'git+https://:password@gitlab.com/foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://gitlab.com/foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://gitlab.com/foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@gitlab.com/foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@gitlab.com/foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@gitlab.com/foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@gitlab.com/foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@gitlab.com/foo/bar',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@gitlab.com/foo/bar#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://gitlab.com/foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://gitlab.com/foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@gitlab.com/foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user@gitlab.com/foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@gitlab.com/foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://user:password@gitlab.com/foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@gitlab.com/foo/bar.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://:password@gitlab.com/foo/bar.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'https://gitlab.com/foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://gitlab.com/foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://user@gitlab.com/foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://user@gitlab.com/foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://user:password@gitlab.com/foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://user:password@gitlab.com/foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://:password@gitlab.com/foo/bar/baz',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://:password@gitlab.com/foo/bar/baz#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://gitlab.com/foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://gitlab.com/foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://user@gitlab.com/foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://user@gitlab.com/foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://user:password@gitlab.com/foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://user:password@gitlab.com/foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://:password@gitlab.com/foo/bar/baz.git',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'https://:password@gitlab.com/foo/bar/baz.git#branch',
        {
            type: 'gitlab',
            url: 'https://gitlab.com/foo/bar/baz/tree/branch',
            host: 'https://gitlab.com',
            owner: 'foo/bar',
            project: 'baz'
        }
    ],
    [
        'sourcehut:~foo/bar',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'sourcehut:~foo/bar#branch',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar/tree/branch',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'sourcehut:~foo/bar.git',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'sourcehut:~foo/bar.git#branch',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar/tree/branch',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'git@git.sr.ht:~foo/bar',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'git@git.sr.ht:~foo/bar#branch',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar/tree/branch',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'git@git.sr.ht:~foo/bar.git',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'git@git.sr.ht:~foo/bar.git#branch',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar/tree/branch',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://git@git.sr.ht:~foo/bar',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://git@git.sr.ht:~foo/bar#branch',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar/tree/branch',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://git@git.sr.ht:~foo/bar.git',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'git+ssh://git@git.sr.ht:~foo/bar.git#branch',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar/tree/branch',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'https://git.sr.ht/~foo/bar',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'https://git.sr.ht/~foo/bar#branch',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar/tree/branch',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'https://git.sr.ht/~foo/bar.git',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'https://git.sr.ht/~foo/bar.git#branch',
        {
            type: 'sourcehut',
            url: 'https://git.sr.ht/~foo/bar/tree/branch',
            host: 'https://git.sr.ht',
            owner: '~foo',
            project: 'bar'
        }
    ],
    [
        'git://localhost:12345/foo/bar',
        {
            type: '',
            url: 'http://localhost:12345/foo/bar',
            host: 'http://localhost:12345',
            owner: 'foo',
            project: 'bar'
        }
    ],
    [
        'git@code.mycompany.com:abc/def.git',
        {
            type: '',
            url: 'https://code.mycompany.com/abc/def',
            host: 'https://code.mycompany.com',
            owner: 'abc',
            project: 'def'
        }
    ],
    [
        'https://unknown-host/.git',
        {
            type: '',
            url: 'https://unknown-host',
            host: 'https://unknown-host'
        }
    ],
    [
        'https://github.internal.example.com/conventional-changelog/internal',
        {
            type: 'github',
            url: 'https://github.internal.example.com/conventional-changelog/internal',
            host: 'https://github.internal.example.com',
            owner: 'conventional-changelog',
            project: 'internal'
        }
    ]
];
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaG9zdGVkR2l0SW5mby5tb2NrLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vc3JjL2hvc3RlZEdpdEluZm8ubW9jay50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQSxNQUFNLENBQUMsTUFBTSxPQUFPLEdBQUc7SUFDckI7UUFDRSxtQkFBbUI7UUFDbkI7WUFDRSxJQUFJLEVBQUUsV0FBVztZQUNqQixHQUFHLEVBQUUsK0JBQStCO1lBQ3BDLElBQUksRUFBRSx1QkFBdUI7WUFDN0IsS0FBSyxFQUFFLEtBQUs7WUFDWixPQUFPLEVBQUUsS0FBSztTQUNmO0tBQ0Y7SUFDRDtRQUNFLDBCQUEwQjtRQUMxQjtZQUNFLElBQUksRUFBRSxXQUFXO1lBQ2pCLEdBQUcsRUFBRSwwQ0FBMEM7WUFDL0MsSUFBSSxFQUFFLHVCQUF1QjtZQUM3QixLQUFLLEVBQUUsS0FBSztZQUNaLE9BQU8sRUFBRSxLQUFLO1NBQ2Y7S0FDRjtJQUNEO1FBQ0Usd0JBQXdCO1FBQ3hCO1lBQ0UsSUFBSSxFQUFFLFdBQVc7WUFDakIsR0FBRyxFQUFFLCtCQUErQjtZQUNwQyxJQUFJLEVBQUUsdUJBQXVCO1lBQzdCLEtBQUssRUFBRSxLQUFLO1lBQ1osT0FBTyxFQUFFLEtBQUs7U0FDZjtLQUNGO0lBQ0Q7UUFDRSwrQkFBK0I7UUFDL0I7WUFDRSxJQUFJLEVBQUUsV0FBVztZQUNqQixHQUFHLEVBQUUsMENBQTBDO1lBQy9DLElBQUksRUFBRSx1QkFBdUI7WUFDN0IsS0FBSyxFQUFFLEtBQUs7WUFDWixPQUFPLEVBQUUsS0FBSztTQUNmO0tBQ0Y7SUFDRDtRQUNFLGlDQUFpQztRQUNqQztZQUNFLElBQUksRUFBRSxXQUFXO1lBQ2pCLEdBQUcsRUFBRSwrQkFBK0I7WUFDcEMsSUFBSSxFQUFFLHVCQUF1QjtZQUM3QixLQUFLLEVBQUUsS0FBSztZQUNaLE9BQU8sRUFBRSxLQUFLO1NBQ2Y7S0FDRjtJQUNEO1FBQ0Usd0NBQXdDO1FBQ3hDO1lBQ0UsSUFBSSxFQUFFLFdBQVc7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