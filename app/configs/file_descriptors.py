import resource
# fd -- file descriptors

def set_fd_limit(n_proxies: int) -> None:
    '''n_proxies: number proxies that we try to connect. One proxy is one session (opend descriptor).
    Set new limit for opened descriptores for current process'''

    # RLIMIT_NOFILE is the max number of open file descriptors
    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    if hard_limit < n_proxies:
        NotImplemented  # should be developed
    elif soft_limit < n_proxies:
        resource.setrlimit(resource.RLIMIT_NOFILE, (n_proxies, hard_limit))
        