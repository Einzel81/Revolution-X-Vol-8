#!/bin/bash
# Revolution X - Backup Script

set -e

BACKUP_DIR="/backups/revolutionx"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30
S3_BUCKET=${BACKUP_S3_BUCKET:-""}

echo "🔧 Starting backup process..."

# Create backup directory
mkdir -p ${BACKUP_DIR}/${DATE}

# Database backup
echo "💾 Backing up database..."
docker-compose -f docker/docker-compose.prod.yml exec -T postgres pg_dump \
    -U ${POSTGRES_USER} \
    -Fc ${POSTGRES_DB} > ${BACKUP_DIR}/${DATE}/db.dump

# Redis backup
echo "💾 Backing up Redis..."
docker-compose -f docker/docker-compose.prod.yml exec -T redis redis-cli BGSAVE
docker cp $(docker-compose -f docker/docker-compose.prod.yml ps -q redis):/data/dump.rdb ${BACKUP_DIR}/${DATE}/redis.rdb

# Application logs
echo "📝 Backing up logs..."
tar -czf ${BACKUP_DIR}/${DATE}/logs.tar.gz -C /var/log/revolutionx .

# Configuration backup
echo "⚙️ Backing up configuration..."
cp -r docker ${BACKUP_DIR}/${DATE}/
cp .env.production ${BACKUP_DIR}/${DATE}/ 2>/dev/null || true

# Compress backup
echo "📦 Compressing backup..."
tar -czf ${BACKUP_DIR}/backup_${DATE}.tar.gz -C ${BACKUP_DIR}/${DATE} .

# Upload to S3 if configured
if [ -n "${S3_BUCKET}" ]; then
    echo "☁️ Uploading to S3..."
    aws s3 cp ${BACKUP_DIR}/backup_${DATE}.tar.gz s3://${S3_BUCKET}/backups/
    
    # Verify upload
    aws s3 ls s3://${S3_BUCKET}/backups/backup_${DATE}.tar.gz
    echo "✅ Upload verified"
fi

# Clean up local backup
rm -rf ${BACKUP_DIR}/${DATE}

# Clean up old backups
echo "🧹 Cleaning up old backups..."
find ${BACKUP_DIR} -name "backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete

# Clean up old S3 backups
if [ -n "${S3_BUCKET}" ]; then
    aws s3 ls s3://${S3_BUCKET}/backups/ | \
    awk '{print $4}' | \
    while read file; do
        date_str=$(echo $file | grep -oP '\d{8}_\d{6}' || true)
        if [ -n "$date_str" ]; then
            file_date=$(date -d "${date_str:0:8}" +%s 2>/dev/null || date -j -f "%Y%m%d" "${date_str:0:8}" +%s)
            cutoff_date=$(date -d "${RETENTION_DAYS} days ago" +%s)
            if [ $file_date -lt $cutoff_date ]; then
                aws s3 rm s3://${S3_BUCKET}/backups/$file
            fi
        fi
    done
fi

echo "✅ Backup complete: backup_${DATE}.tar.gz"
