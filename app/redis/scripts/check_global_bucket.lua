local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate_per_sec = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- Read current state from Redis Hash
local bucket = redis.call('HMGET', key, 'tokens', 'last_refill_ts')
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

-- Initialize if it doesn't exist
if not tokens then
    tokens = capacity
    last_refill = now
else
    -- Calculate tokens to add based on time elapsed
    local elapsed = math.max(0, now - last_refill)
    local added = math.floor(elapsed * refill_rate_per_sec)
    if added > 0 then
        tokens = math.min(capacity, tokens + added)
        last_refill = now
    end
end

local allowed = 0
if tokens > 0 then
    allowed = 1
    tokens = tokens - 1
    -- Save the updated state
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill_ts', last_refill)
    -- Set a TTL to clean up idle keys
    redis.call('EXPIRE', key, math.ceil(capacity / refill_rate_per_sec) * 2)
end

-- Calculate time until bucket is full again
local reset_seconds = 0
if tokens < capacity then
    reset_seconds = math.ceil((capacity - tokens) / refill_rate_per_sec)
end

-- Must return exactly what the FR requires
return {allowed, tokens, reset_seconds}