"""
Access and helper functions for the status table.
"""
import datetime as dt
import logging
import re

from ..tools.exec_utils import get_url

LOG = logging.getLogger()

def compute_database_date(conn):
    """ Determine the date of the database from the newest object in the
        data base.
    """
    # First, find the node with the highest ID in the database
    with conn.cursor() as cur:
        osmid = cur.scalar("SELECT max(osm_id) FROM place WHERE osm_type='N'")

        if osmid is None:
            LOG.fatal("No data found in the database.")
            raise RuntimeError("No data found in the database.")

    LOG.info("Using node id %d for timestamp lookup", osmid)
    # Get the node from the API to find the timestamp when it was created.
    node_url = 'https://www.openstreetmap.org/api/0.6/node/{}/1'.format(osmid)
    data = get_url(node_url)

    match = re.search(r'timestamp="((\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2}))Z"', data)

    if match is None:
        LOG.fatal("The node data downloaded from the API does not contain valid data.\n"
                  "URL used: %s", node_url)
        raise RuntimeError("Bad API data.")

    LOG.debug("Found timestamp %s", match[1])

    return dt.datetime.fromisoformat(match[1]).replace(tzinfo=dt.timezone.utc)


def set_status(conn, date, seq=None, indexed=True):
    """ Replace the current status with the given status.
    """
    assert date.tzinfo == dt.timezone.utc
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE import_status")
        cur.execute("""INSERT INTO import_status (lastimportdate, sequence_id, indexed)
                       VALUES (%s, %s, %s)""", (date, seq, indexed))

    conn.commit()
