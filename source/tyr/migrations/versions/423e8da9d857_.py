# Copyright (c) 2001-2014, Canal TP and/or its affiliates. All rights reserved.
#   
# This file is part of Navitia,
#     the software to build cool stuff with public transport.
#  
# Hope you'll enjoy and contribute to this project,
#     powered by Canal TP (www.canaltp.fr).
# Help us simplify mobility and open public transport:
#     a non ending quest to the responsive locomotion way of traveling!
#   
# LICENCE: This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#    
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#    
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#   
# Stay tuned using
# twitter @navitia 
# IRC #navitia on freenode
# https://groups.google.com/d/forum/navitia
# www.navitia.io

"""Split Job in two: the Job for the actual task and DataSet for the data being loaded

Revision ID: 423e8da9d857
Revises: 1fd68e6d0456
Create Date: 2014-01-13 08:17:34.864950

"""

# revision identifiers, used by Alembic.
revision = '423e8da9d857'
down_revision = '1fd68e6d0456'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('data_set',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Text(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['job.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    #enum are not automatically created, so we create it
    #workaround from: https://bitbucket.org/zzzeek/alembic/issue/89/opadd_column-and-opdrop_column-should
    enum = sa.Enum('pending', 'running', 'done', 'failed', name='job_state')
    bind = op.get_bind()
    impl = enum.dialect_impl(bind.dialect)
    impl.create(bind, checkfirst=True)

    op.add_column('job',
        sa.Column('state', enum)
    )
    op.drop_column(u'job', 'type')
    op.drop_column(u'job', 'filename')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'job', sa.Column('filename', sa.TEXT(), nullable=True))
    op.add_column(u'job', sa.Column('type', sa.TEXT(), nullable=True))
    op.drop_table('data_set')
    ### end Alembic commands ###
