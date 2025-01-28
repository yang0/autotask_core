import sqlite3
import logging
import json
from typing import Dict, Any, AsyncIterator, List, Optional, Set
from pathlib import Path
try:
    from autotask.knowledge.documentManager import register_loader
    from autotask.knowledge.documentManager import DocumentLoader
except ImportError:
    from ..stub import register_loader, DocumentLoader

logger = logging.getLogger(__name__)

@register_loader(['sqlite3', 'db'])
class SQLiteLoader(DocumentLoader):
    """SQLite文件加载器"""
    
    def __init__(self):
        self.table_stats_cache = {}  # 缓存表状态
    
    def _get_table_stats(self, conn: sqlite3.Connection, table_name: str) -> Dict[str, Any]:
        """获取表的统计信息"""
        cursor = conn.cursor()
        # 获取表的行数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # 获取最后一条记录的修改时间（如果表有update_time字段）
        try:
            cursor.execute(f"SELECT MAX(update_time) FROM {table_name}")
            last_update = cursor.fetchone()[0]
        except:
            last_update = None
            
        return {
            "row_count": row_count,
            "last_update": last_update
        }
    
    def _table_needs_update(
        self,
        table_name: str,
        current_stats: Dict[str, Any],
        cached_stats: Optional[Dict[str, Any]]
    ) -> bool:
        """判断表是否需要更新"""
        if not cached_stats:
            return True
            
        if current_stats["row_count"] != cached_stats["row_count"]:
            return True
            
        if (current_stats["last_update"] and cached_stats["last_update"] and 
            current_stats["last_update"] > cached_stats["last_update"]):
            return True
            
        return False

    async def load(self, source: Path) -> AsyncIterator[Dict[str, Any]]:
        """加载SQLite数据库内容，支持增量更新"""
        try:
            conn = sqlite3.connect(source)
            cursor = conn.cursor()
            
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            # 获取当前表状态
            current_table_stats = {}
            for (table_name,) in tables:
                current_table_stats[table_name] = self._get_table_stats(conn, table_name)
            
            # 读取缓存的表状态
            cache_file = source.parent / f"{source.name}.tablestats"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        self.table_stats_cache = json.load(f)
                except:
                    self.table_stats_cache = {}
            
            for (table_name,) in tables:
                # 检查表是否需要更新
                if not self._table_needs_update(
                    table_name,
                    current_table_stats[table_name],
                    self.table_stats_cache.get(table_name)
                ):
                    logger.info(f"Skipping unchanged table: {table_name}")
                    continue
                
                try:
                    # 获取表结构和主键信息
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns_info = cursor.fetchall()
                    columns = [col[1] for col in columns_info]
                    
                    # 找出主键列
                    pk_columns = [col[1] for col in columns_info if col[5] > 0]
                    if not pk_columns:
                        pk_columns = columns
                    
                    # 获取表数据
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        row_id = ":".join(str(row_dict[pk_col]) for pk_col in pk_columns)
                        
                        yield {
                            "id": f"{source}:{table_name}:{row_id}",
                            "content": str(row_dict),
                            "metadata": {
                                "source": str(source),
                                "table_name": table_name,
                                "primary_keys": pk_columns,
                                "row_id": row_id,
                                "columns": columns
                            }
                        }
                    
                    # 更新表状态缓存
                    self.table_stats_cache[table_name] = current_table_stats[table_name]
                    
                except Exception as e:
                    logger.error(f"Error processing table {table_name} in {source}: {str(e)}")
                    continue
            
            # 保存表状态缓存
            with open(cache_file, 'w') as f:
                json.dump(self.table_stats_cache, f)
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Error opening SQLite database {source}: {str(e)}")
            yield None
