import { useEffect, useRef, useCallback } from 'react';

/**
 * Hook for infinite scrolling using IntersectionObserver
 * @param {Function} onLoadMore - Callback function to load more items
 * @param {Object} options - IntersectionObserver options
 * @param {boolean} hasMore - Condition to check if more items are available
 * @param {boolean} isLoading - Condition to prevent multiple calls while loading
 * @returns {Object} { loaderRef } - Ref to attach to the sentinel element
 */
export function useInfiniteScroll(onLoadMore, { threshold = 1.0, rootMargin = '20px' } = {}, hasMore = true, isLoading = false) {
    const loaderRef = useRef(null);

    const handleObserver = useCallback((entries) => {
        const target = entries[0];
        if (target.isIntersecting && hasMore && !isLoading) {
            onLoadMore();
        }
    }, [onLoadMore, hasMore, isLoading]);

    useEffect(() => {
        const option = {
            root: null, // viewport
            rootMargin,
            threshold
        };
        const observer = new IntersectionObserver(handleObserver, option);

        const currentLoaderRef = loaderRef.current;
        if (currentLoaderRef) {
            observer.observe(currentLoaderRef);
        }

        return () => {
            if (currentLoaderRef) {
                observer.unobserve(currentLoaderRef);
            }
        };
    }, [handleObserver, rootMargin, threshold]);

    return { loaderRef };
}
