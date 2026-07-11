local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local req_id = ARGV[4] -- A UUID to prevent ZSET element collisions

local window_start = now - window_seconds

-- 1. Prune requests older than the sliding window
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)

-- 2. Count current valid requests
local current_requests = tonumber(redis.call('ZCARD', key)) or 0

local allowed = 0
if current_requests < limit then
    allowed = 1
    -- 3. Add the current request to the window
    redis.call('ZADD', key, now, req_id)
    current_requests = current_requests + 1
end

-- Refresh TTL so idle tenants drop out of memory
redis.call('EXPIRE', key, window_seconds)

local remaining = math.max(0, limit - current_requests)

-- Output matches the specification contract
return {allowed, remaining, window_seconds}